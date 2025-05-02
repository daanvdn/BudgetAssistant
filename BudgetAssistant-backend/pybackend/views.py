import io
import json
import traceback
from datetime import datetime
from email.message import EmailMessage
from typing import Dict, List, Optional, Union

from django.contrib.auth import get_user_model, logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetConfirmView, PasswordResetView
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.files.uploadedfile import UploadedFile
from django.core.mail import EmailMessage
from django.db.models import QuerySet
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseServerError, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode
from drf_spectacular.utils import PolymorphicProxySerializer, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.exceptions import UnsupportedMediaType, ValidationError
from rest_framework.fields import BooleanField
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.serializers import CharField, EmailField
from rest_framework.views import APIView

from pybackend.analysis import BudgetTrackerResult, BudgetTrackerResultSerializer, \
    CategoryDetailsForPeriodHandlerResult, \
    CategoryDetailsForPeriodHandlerResultSerializer, \
    ExpensesAndRevenueForPeriod, RevenueAndExpensesPerPeriodAndCategory, \
    RevenueAndExpensesPerPeriodAndCategorySerializer
from pybackend.categorization import RuleBasedCategorizer
from pybackend.commons import RevenueExpensesQuery, RevenueExpensesQuerySerializer, RevenueExpensesQueryWithCategory, \
    RevenueExpensesQueryWithCategorySerializer, TransactionTypeEnum
from pybackend.dto import BankAccountNumberSerializer, CategorizeTransactionsResponse, \
    CategorizeTransactionsResponseSerializer, Count, \
    CountSerializer, FailedOperationResponse, FailedOperationResponseSerializer, GetOrCreateRuleSetWrapper, \
    GetOrCreateRuleSetWrapperSerializer, PageTransactionsInContextRequest, \
    PageTransactionsInContextRequestSerializer, PageTransactionsRequest, \
    PageTransactionsRequestSerializer, \
    PageTransactionsToManuallyReviewRequest, PageTransactionsToManuallyReviewRequestSerializer, RegisterUser, \
    RegisterUserSerializer, \
    RevenueAndExpensesPerPeriodResponse, \
    RevenueAndExpensesPerPeriodResponseSerializer, SaveAlias, SaveAliasSerializer, \
    SuccessfulOperationResponse, \
    SuccessfulOperationResponseSerializer, \
    TransactionsPage, \
    TransactionsPageSerializer, UploadTransactionsResponseSerializer
from pybackend.models import BankAccount, BudgetTreeNode, CustomUser, Transaction
from pybackend.period import ResolvedStartEndDateShortcutSerializer
from pybackend.providers import BudgetTreeProvider, CategoryTreeProvider
from pybackend.rules import RuleSerializer, RuleSetWrapperSerializer
from pybackend.serializers import BankAccountSerializer, BudgetTreeNodeSerializer, BudgetTreeSerializer, \
    CategoryTreeSerializer, TransactionSerializer
from pybackend.services import AnalysisService, BankAccountsService, BudgetTreeService, PeriodService, RuleSetsService, \
    TransactionsService
from pybackend.transactions_parsing import BelfiusTransactionParser

# fixme: https://chatgpt.com/share/6765edf9-dcd4-800d-bd3e-686763a1e643

expenses_category_tree = None
revenue_category_tree = None
rule_based_categorizer = None
bank_accounts_service = None
transactions_service = None
budget_tree_service = None
rule_sets_service = None
analysis_service = None
period_service = None


def get_period_service():
    global period_service
    if not period_service:
        period_service = PeriodService()
    return period_service


def get_analysis_service():
    global analysis_service
    if not analysis_service:
        analysis_service = AnalysisService()
    return analysis_service


def get_rule_sets_service():
    global rule_sets_service
    if not rule_sets_service:
        rule_sets_service = RuleSetsService()
    return rule_sets_service


def get_budget_tree_service():
    global budget_tree_service
    if not budget_tree_service:
        budget_tree_service = BudgetTreeService()
    return budget_tree_service


def get_transactions_service():
    global transactions_service
    if not transactions_service:
        transactions_service = TransactionsService()
    return transactions_service


def get_bank_accounts_service():
    global bank_accounts_service
    if not bank_accounts_service:
        bank_accounts_service = BankAccountsService()
    return bank_accounts_service


def get_rule_based_categorizer():
    global rule_based_categorizer
    if not rule_based_categorizer:
        rule_based_categorizer = RuleBasedCategorizer(expenses_category_tree=get_expenses_category_tree(),
                                                      revenue_category_tree=get_revenue_category_tree())
    return rule_based_categorizer


def get_revenue_category_tree():
    global revenue_category_tree
    if not revenue_category_tree:
        revenue_category_tree = CategoryTreeProvider().provide(type=TransactionTypeEnum.REVENUE)
    return revenue_category_tree


def get_expenses_category_tree():
    global expenses_category_tree
    if not expenses_category_tree:
        expenses_category_tree = CategoryTreeProvider().provide(type=TransactionTypeEnum.EXPENSES)
    return expenses_category_tree


from drf_spectacular.utils import OpenApiParameter
from drf_spectacular.types import OPENAPI_TYPE_MAPPING, PYTHON_TYPE_MAPPING

# create reversed map of PYTHON_TYPE_MAPPING
PYTHON_TYPE_MAPPING_REVERSED = {v.name: k for k, v in PYTHON_TYPE_MAPPING.items()}


def create_openapi_type_to_pythion_type_mapping():
    map = {}
    for openapi_type, json_repr in OPENAPI_TYPE_MAPPING.items():
        if openapi_type.name not in PYTHON_TYPE_MAPPING_REVERSED:
            continue
        python_type = PYTHON_TYPE_MAPPING_REVERSED[openapi_type.name]
        json_repr: Dict = json_repr
        map[json.dumps(json_repr, sort_keys=True)] = python_type
    return map


# JSON_TYPE_REPR_TO_PYTHON_TYPE_MAPPING = create_openapi_type_to_pythion_type_mapping()





def pydantic_to_openapi_parameters(model):
    """
    Convert a Pydantic model to a list of OpenApiParameter objects, handling `anyOf` and `oneOf`.
    """
    schema = model.model_json_schema()
    parameters = []
    remove_dto_suffix_case_insensitive = lambda name: name[:-3] if name.lower().endswith("dto") else name

    def extract_type(details):
        """
        Extract the OpenAPI type from a JSON Schema definition, handling nullable types, `anyOf`, and `oneOf`.
        """
        openapi_types = []
        if "anyOf" in details or "oneOf" in details:
            key = "anyOf" if "anyOf" in details else "oneOf"
            entries = [entry for entry in details[key] if "type" in entry]

        details_copy = {}
        if 'type' in details:
            details_copy['type'] = details['type']
        if 'format' in details:
            details_copy['format'] = details['format']

        if "anyOf" in details or "oneOf" in details:
            key = "anyOf" if "anyOf" in details else "oneOf"
            types = [entry.get("type") for entry in details[key] if "type" in entry]
            if "null" in types:
                types.remove("null")
                # Combine with `nullable` if there's exactly one remaining type
                return types[0] if len(types) == 1 else 'string'
            return 'string'  # Default for complex cases
        return 'string'  # Fallback for unsupported or missing type information

    def is_nullable(details):
        """
        Determine if a field is nullable based on `anyOf` or `oneOf`.
        """
        for key in ["anyOf", "oneOf"]:
            if key in details:
                types = [entry.get("type") for entry in details[key] if "type" in entry]
                if "null" in types:
                    return True
        return False

    for name, details in schema.get("properties", {}).items():
        _type = extract_type(details)
        parameter = OpenApiParameter(
            name=remove_dto_suffix_case_insensitive(name),
            type=_type,
            description=details.get("description", ""),
            required=name in schema.get("required", []),
            allow_blank=is_nullable(details)
        )
        parameters.append(parameter)

    return parameters


#TRANSACTION_DTO_PARAMETERS = pydantic_to_openapi_parameters(TransactionDTO)
BANK_ACCOUNT_NUMBER_PARAM = OpenApiParameter(name='bank_account', type=str, description='the bankaccount number',
                                              required=True)
TRANSACTION_TYPE_PARAM = OpenApiParameter(name='transaction_type', type=str, description='the transaction type',
                                           required=True, enum=[TransactionTypeEnum.EXPENSES.value, TransactionTypeEnum.REVENUE.value, TransactionTypeEnum.BOTH.value])
#REVENUE_EXPENSES_QUERY_PARAMS: List[OpenApiParameter] = pydantic_to_openapi_parameters(RevenueExpensesQuery)

EXPENSES_OR_REVENUE_PARAM = OpenApiParameter(name='transaction_type', type=str, description='the transaction type',
                                             required=True, enum=[TransactionTypeEnum.EXPENSES.value, TransactionTypeEnum.REVENUE.value])

STRING_LIST_RESPONSE = {"type": "array", "items": {"type": "string"}}

def home(request):
    return HttpResponse("Welcome to the home page!")


class CustomLogoutView(APIView):
    @extend_schema(
        request=None,
        responses={
            200: inline_serializer(
                name='LogoutResponse',
                fields={'message': CharField()}
            )
        }
    )
    def post(self, request, *args, **kwargs):
        logout(request)
        request.session.flush()  # Clear all session data
        return JsonResponse({'message': 'Logged out successfully'}, status=200)

class BankAccountsForUserView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: BankAccountSerializer(many=True)})
    def get(self, request):
        user = request.user
        if not isinstance(user, CustomUser):
            raise ValueError(f"User must be an instance of CustomUser. Received {type(user)}")
        bank_accounts = get_bank_accounts_service().find_distinct_by_users_contains(user)
        # use BankAccountSerializer to serialize the bank accounts
        serializer = BankAccountSerializer(bank_accounts, many=True)
        return JsonResponse(serializer.data, status=200, safe=False)


class RevenueAndExpensesPerPeriodView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        # request=OpenApiRequest(request=RevenueExpensesQuerySerializer),
        request=RevenueExpensesQuerySerializer,
        responses={
            200: RevenueAndExpensesPerPeriodResponseSerializer,
            204: None,
            500: None
        }
    )
    def post(self, request, *args, **kwargs):
        decode = request.body.decode('utf-8')
        serializer = RevenueExpensesQuerySerializer(data=json.loads(decode))
        if serializer.is_valid():
            validated_data = serializer.validated_data
            revenue_expenses_query = RevenueExpensesQuery(**validated_data)

            if revenue_expenses_query.is_empty():
                return None
            expenses_and_revenue_per_period: Optional[
                List[ExpensesAndRevenueForPeriod]] = get_analysis_service().get_revenue_and_expenses_per_period(
                revenue_expenses_query)
            if not expenses_and_revenue_per_period:
                return JsonResponse({}, status=204)

            def create_response(data) -> RevenueAndExpensesPerPeriodResponse:
                result = dict()
                result["content"] = data or []
                result["number"] = 1 if data else 0
                result["total_elements"] = len(data) if data else 0
                result["size"] = len(data) if data else 0

                return RevenueAndExpensesPerPeriodResponse(**result)

            try:
                response_obj = create_response(expenses_and_revenue_per_period)
                return JsonResponse(RevenueAndExpensesPerPeriodResponseSerializer(response_obj).data, safe=False)

            except Exception as e:
                return HttpResponseServerError()
        else:
            return JsonResponse({}, status=500)

class PageTransactionsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=PageTransactionsRequestSerializer,
        responses={
            200: TransactionsPageSerializer,
            400: None
        })
    def post(self, request, *args, **kwargs):
        try:
            body = json.loads(request.body.decode('utf-8'))
            serializer = PageTransactionsRequestSerializer(data=body)
            if serializer.is_valid(raise_exception=True):
                user: CustomUser = request.user

                page_transactions_request = PageTransactionsRequest(**serializer.validated_data)
                query = page_transactions_request.query
                page = page_transactions_request.page
                size = page_transactions_request.size
                sort_order = page_transactions_request.sort_order
                sort_property = page_transactions_request.sort_property
                response: TransactionsPage = get_transactions_service().page_transactions(query, page, size, sort_order,
                                                                                          sort_property, user)
                data = TransactionsPageSerializer(response).data
                return JsonResponse(data, status=200)

        except Exception as e:
            traceback.print_exc()
            return JsonResponse({}, status=400)


class PageTransactionsInContextView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=PageTransactionsInContextRequestSerializer,
        responses={
            200: TransactionsPageSerializer,
            500: None,
            400: None
        })
    def post(self, request, *args, **kwargs):
        request_serializer = PageTransactionsInContextRequestSerializer(data=json.loads(request.body.decode('utf-8')))
        if request_serializer.is_valid():
            request_obj = PageTransactionsInContextRequest(**request_serializer.validated_data)
            query = request_obj.query
            page = request_obj.page
            size = request_obj.size
            sort_order = request_obj.sort_order
            sort_property = request_obj.sort_property
            response: TransactionsPage = get_transactions_service().page_transactions_in_context(query, page, size,
                                                                                                 sort_order,
                                                                                                 sort_property)
            return JsonResponse(TransactionsPageSerializer(response).data, status=200)

        else:
            return JsonResponse({}, status=400)

class PageTransactionsToManuallyReviewView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=PageTransactionsToManuallyReviewRequestSerializer,
        responses={
            200: TransactionsPageSerializer,
            400: None,
            500: None
        })
    def post(self, request, *args, **kwargs):
        body = json.loads(request.body.decode('utf-8'))
        serializer = PageTransactionsToManuallyReviewRequestSerializer(data=body)

        if serializer.is_valid():
            request_obj = PageTransactionsToManuallyReviewRequest(**serializer.validated_data)
            bank_account = request_obj.bank_account
            page = request_obj.page
            size = request_obj.size
            sort_order = request_obj.sort_order
            sort_property = request_obj.sort_property
            transaction_type = request_obj.transaction_type
            transactions_page_dto: TransactionsPage = get_transactions_service().page_transactions_to_manually_review(
                bank_account, page, size, sort_order,
                sort_property, transaction_type)
        else:
            return JsonResponse({}, status=400)

        return JsonResponse(TransactionsPageSerializer(transactions_page_dto).data, status=200)

class CountTransactionsToManuallyReviewView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[BANK_ACCOUNT_NUMBER_PARAM],
        responses={
            200: CountSerializer,
            500: None
        })
    def get(self, request):
        bank_account = request.query_params.get('bank_account')
        count = get_transactions_service().count_transactions_to_manually_review(bank_account)
        return JsonResponse(CountSerializer(Count(count=count)).data, status=200)


def serialize_succesful_or_failed_operation_reponse(response: Union[
    SuccessfulOperationResponse, FailedOperationResponse]) -> Dict:
    if isinstance(response, SuccessfulOperationResponse):
        serializer = SuccessfulOperationResponseSerializer(response)

    elif isinstance(response, FailedOperationResponse):
        serializer = FailedOperationResponseSerializer(response)
    else:
        raise ValueError(f"Invalid response type {type(response)}")
    return serializer.data

class SaveTransactionView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=TransactionSerializer,
        responses={
            200: SuccessfulOperationResponseSerializer,
            400: FailedOperationResponseSerializer,
            500: FailedOperationResponseSerializer
        })
    def post(self, request):
        try:
            body = request.body
            # body is a bytes object, so we need to convert it to a string
            decode = body.decode('utf-8')
            transaction_json = json.loads(decode)
            response: Union[
                SuccessfulOperationResponse, FailedOperationResponse] = get_transactions_service().save_transaction(
                transaction_json)

            return JsonResponse(serialize_succesful_or_failed_operation_reponse(response), status=response.status_code)
        except Exception as e:
            return JsonResponse(
                serialize_succesful_or_failed_operation_reponse(FailedOperationResponse(error=str(e), status_code=500)),
                status=500)

class CategoryTreeView(APIView):

    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[EXPENSES_OR_REVENUE_PARAM],
        responses={
            200: CategoryTreeSerializer,
            500: None,
            400 : str
        }
    )
    def get(self, request, *args, **kwargs):
        try:
            transaction_type = TransactionTypeEnum[request.query_params.get('transaction_type')]
            if transaction_type == TransactionTypeEnum.EXPENSES:
                category_tree = get_expenses_category_tree()
            elif transaction_type == TransactionTypeEnum.REVENUE:
                category_tree = get_revenue_category_tree()
            else:
                return HttpResponseBadRequest("Invalid transaction type")
            return JsonResponse(CategoryTreeSerializer(category_tree).data, safe=False, status=200)
        except Exception as e:
            traceback.print_exc()
            return HttpResponseServerError()

class DistinctCounterpartyNamesView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[BANK_ACCOUNT_NUMBER_PARAM],
        responses= {
            #for status 200, the response is a list of strings
            200: STRING_LIST_RESPONSE,
            500: None
        })
    def get(self, request):
        try:
            account = request.query_params.get('account')
            account = BankAccount.normalize_account_number(account)
            names: QuerySet = Transaction.objects.find_distinct_counterparty_names(account)
            # convert this QuerySet to a list
            names_list = list(names)
            # convert the list to a json response
            return JsonResponse(names_list, safe=False, status=200)
        except Exception as e:
            traceback.print_exc()
            return HttpResponseServerError()

class DistinctCounterpartyAccountsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[BANK_ACCOUNT_NUMBER_PARAM],
        responses= {
            #for status 200, the response is a list of strings
            200: STRING_LIST_RESPONSE,
            500: None
        })
    def get(self, request):
        try:
            account = request.data.get('bank_account')
            account_numbers: QuerySet = Transaction.objects.find_distinct_counterparty_account_numbers(account)
            # convert this QuerySet to a list
            account_numbers_list = list(account_numbers)
            # convert the list to a json response
            return JsonResponse(account_numbers_list, safe=False, status=200)
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({}, status=500)

class UploadTransactionsView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'files': {
                        'type': 'array',
                        'items': {'type': 'string', 'format': 'binary'}
                    }
                }
            }
        },
        responses={
            200: UploadTransactionsResponseSerializer,
            500: None
        }
    )
    def post(self, request, *args, **kwargs):
        try:
            if not request.content_type.startswith('multipart/form-data'):
                raise UnsupportedMediaType(request.content_type)
            files: List[UploadedFile] = request.FILES.getlist('files')
            user = request.user
            if not isinstance(user, CustomUser):
                raise ValueError(f"User must be an instance of CustomUser. Received {type(user)}")

            def serialize_deserialize_datetime(dt: datetime) -> datetime:
                data = serializers.DateTimeField().to_representation(dt)
                #convert data back to datetime
                return serializers.DateTimeField().to_internal_value(data)

            upload_timestamp = datetime.now()

            created = 0
            updated = 0
            for file in files:
                decoded_file = io.TextIOWrapper(file, encoding='utf-8')
                lines = decoded_file.readlines()  # Reads all lines as a list
                parse_result = get_transactions_service().upload_transactions(lines, user, upload_timestamp,
                                                                              BelfiusTransactionParser(), file.name)
                created += parse_result.created
                updated += parse_result.updated
            return JsonResponse({'created': created, 'updated': updated, 'upload_timestamp': serializers.DateTimeField().to_representation(upload_timestamp)}, status=200)
        except UnsupportedMediaType as e:
            return JsonResponse({'error': f'Unsupported media type: {str(e)}'}, status=415)
        except Exception as e:
            traceback.print_exc()
            return HttpResponseServerError()

class RevenueExpensesPerPeriodAndCategoryView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=RevenueExpensesQuerySerializer,
        responses={
            200: RevenueAndExpensesPerPeriodAndCategorySerializer,
            204: RevenueAndExpensesPerPeriodAndCategorySerializer,
            500: None,
            400: None
        })
    def post(self, request, *args, **kwargs):
        try:
            query = request.body.decode('utf-8')
            serializer = RevenueExpensesQuerySerializer(data=json.loads(query))
            if serializer.is_valid():
                validated_data = serializer.validated_data
                revenue_expenses_query = RevenueExpensesQuery(**validated_data)
                result = get_analysis_service().get_revenue_and_expenses_per_period_and_category(revenue_expenses_query)
                if not result:

                    return JsonResponse(RevenueAndExpensesPerPeriodAndCategorySerializer(
                        RevenueAndExpensesPerPeriodAndCategory.empty_instance()).data, status=204, safe=False)
                else:
                    return JsonResponse(RevenueAndExpensesPerPeriodAndCategorySerializer(result).data,
                                        status=200, safe=False)
            else:
                # bad request
                return JsonResponse({}, status=400)
        except Exception as e:
            traceback.print_exc()
            return HttpResponseServerError()


class TrackBudgetView(APIView):

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=RevenueExpensesQuerySerializer(),
        responses={
            200: BudgetTrackerResultSerializer,
            500: None,
            400: None
        })
    def post(self, request):
        try:
            body: str = request.body.decode('utf-8')
            serializer = RevenueExpensesQuerySerializer(data=json.loads(body))
            if serializer.is_valid():
                validated_data = serializer.validated_data
                query_obj = RevenueExpensesQuery(**validated_data)
                result: Optional[BudgetTrackerResult] = get_analysis_service().track_budget(query_obj)
                if not result:
                    return JsonResponse({}, status=204)
                return JsonResponse(BudgetTrackerResultSerializer(result).data, status=200)

            else:
                # bad request
                return JsonResponse({}, status=400)
        except Exception as e:
            traceback.print_exc()
            return HttpResponseServerError()


class RevenueExpensesPerPeriodAndCategoryShow1MonthBeforeAndAfterView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: RevenueAndExpensesPerPeriodAndCategorySerializer,
            500: None
        })
    def get(self, request):
        # Implement logic to get revenue and expenses per period and category, showing 1 month before and after
        pass

class ResolveStartEndDateShortcutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[OpenApiParameter(
            name='query', type=str,
            enum=["current month", "previous month", "current quarter", "previous quarter", "current year",
                  "previous year",
                  "all"], required=True)],
        responses={
            200: ResolvedStartEndDateShortcutSerializer,
            500: None
        }
    )
    def get(self, request):
        try:
            # Implement logic to resolve start and end date shortcut
            query: str = request.query_params.get('query')
            if not query:
                return HttpResponseBadRequest()

            return JsonResponse(ResolvedStartEndDateShortcutSerializer(get_period_service().resolve_start_end_date_shortcut(query)).data, status=200)
        except:
            return HttpResponseServerError()

@extend_schema(auth=[])
class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=RegisterUserSerializer,
                   responses={
                       201: SuccessfulOperationResponseSerializer,
                       400: FailedOperationResponseSerializer,
                       500: None
                   })
    def post(self, request, *args, **kwargs):
        try:
            UserModel: CustomUser = get_user_model()
            body = request.body.decode('utf-8')
            serializer = RegisterUserSerializer(data= json.loads(body))
            if serializer.is_valid():
                register_user_dto = RegisterUser(**serializer.validated_data)
                username = register_user_dto.username
                password = register_user_dto.password
                email = register_user_dto.email
                error_messages = []
                if len(password) < 8:
                    error_messages.append('Password must be at least 8 characters long')

                if len(username) < 4:
                    error_messages.append('Username must be at least 4 characters long')
                if len(email) < 8:
                    error_messages.append('Email must be at least 4 characters long')

                if UserModel.objects.filter(username=username).exists():
                    error_messages.append('Username already exists')
                if len(error_messages) > 0:
                    return JsonResponse(serialize_succesful_or_failed_operation_reponse(
                        FailedOperationResponse(error="\n".join(error_messages),
                                                status_code=status.HTTP_400_BAD_REQUEST)),
                                        status=status.HTTP_400_BAD_REQUEST)

                user: CustomUser = UserModel.objects.create_user(username=username, email=email, password=password)
                return JsonResponse(serialize_succesful_or_failed_operation_reponse(
                    SuccessfulOperationResponse(message=f"User '{user.username}' created successfully")),
                                    status=status.HTTP_201_CREATED)
            else:
                def format_value(val: List[str]):
                    if not isinstance(val, list):
                        raise ValueError(f"Expected a list, received {type(val)}")
                    if len(val) == 1:
                        return str(val[0])
                    if len(val) == 0:
                        raise ValueError("Expected a list with at least one element")
                    return "\n".join([f"\t- {str(item)}" for item in val])
                error_msgs = []
                for key, value in serializer.errors.items():
                    error_msgs.append(f"{key}:\n{format_value(value)}")
                return JsonResponse(FailedOperationResponseSerializer(FailedOperationResponse("\n".join(error_msgs), 400)).data, status=400)
        except Exception as e:
            traceback.print_exc()
            return HttpResponseServerError()


class UpdateUserView(APIView):


    """
    View to update the authenticated user's password or email address.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=PolymorphicProxySerializer(
            component_name='PasswordEmail',
            serializers=[
                inline_serializer(name='password', fields={'password': CharField()}),
                inline_serializer(name='email', fields={'email': CharField()}),
            ],
            resource_type_field_name=None,
        ),
        responses={
            200: {"type": "object", "properties": {"message": {"type": "string"}}},
            400: {"type": "object", "properties": {"errors": {"type": "array", "items": {"type": "string"}}}},
            500: None
        }
    )

    def put(self, request):
        try:
            user = request.user
            data = request.data

            # Handle password change
            if "password" in data:
                try:
                    new_password = data["password"]
                    validate_password(new_password, user)
                    user.set_password(new_password)
                    user.save()
                    return JsonResponse(
                        serialize_succesful_or_failed_operation_reponse(
                            SuccessfulOperationResponse(message="Password updated successfully.")),
                        status=status.HTTP_200_OK)
                except DjangoValidationError as e:
                    return JsonResponse(serialize_succesful_or_failed_operation_reponse(
                        FailedOperationResponse(error="\n".join([message for message in e.messages]),
                                                status_code=status.HTTP_400_BAD_REQUEST)),
                        status=status.HTTP_400_BAD_REQUEST)
                except ValidationError as e:
                    return JsonResponse(serialize_succesful_or_failed_operation_reponse(
                        FailedOperationResponse(error="\n".join([str(item) for item in e.detail]),
                                                status_code=status.HTTP_400_BAD_REQUEST)),
                        status=status.HTTP_400_BAD_REQUEST)

            # Handle email change
            if "email" in data:
                new_email = data["email"]
                try:
                    # Validate the email format
                    email_serializer = EmailField()
                    email_serializer.run_validation(new_email)
                    user.email = new_email
                    user.save()
                    return JsonResponse(serialize_succesful_or_failed_operation_reponse(
                        SuccessfulOperationResponse(message="Email updated successfully.")), status=status.HTTP_200_OK)
                except DjangoValidationError as e:
                    return JsonResponse(serialize_succesful_or_failed_operation_reponse(
                        FailedOperationResponse(error="\n".join([message for message in e.messages]),
                                                status_code=status.HTTP_400_BAD_REQUEST)),
                        status=status.HTTP_400_BAD_REQUEST)
                except ValidationError as e:
                    return JsonResponse(serialize_succesful_or_failed_operation_reponse(
                        FailedOperationResponse(error="\n".join([str(item) for item in e.detail]),
                                                status_code=status.HTTP_400_BAD_REQUEST)),
                        status=status.HTTP_400_BAD_REQUEST)

            return JsonResponse(serialize_succesful_or_failed_operation_reponse(
                FailedOperationResponse(error="No valid fields provided for update.",
                                        status_code=status.HTTP_400_BAD_REQUEST))
                                , status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            traceback.print_exc()
            return HttpResponseServerError()


class UpdateBudgetEntryAmountView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=BudgetTreeNodeSerializer,
        responses={
            200: {},
            400: {},
            500: {}
        })
    def post(self, request):
        try:
            body = request.body.decode('utf-8')
            body = json.loads(body)
            budget_tree_node_instance = BudgetTreeNode.objects.get(pk=body['budget_tree_node_id'])

            serializer = BudgetTreeNodeSerializer(budget_tree_node_instance, data=body)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return JsonResponse({}, status=200)
            else:
                return JsonResponse({}, status=400)
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({}, status=500)


class FindOrCreateBudgetView(APIView):

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=BankAccountNumberSerializer,
        responses={
            200: BudgetTreeSerializer,
            404: {},
            500: {}
        })
    def post(self, request, *args, **kwargs):
        body = json.loads(request.body.decode('utf-8'))
        bank_account_number = body.get('bank_account_number')
        bank_account = get_object_or_404(BankAccount, account_number=bank_account_number)
        budget_tree = BudgetTreeProvider().provide(bank_account)
        json_data = BudgetTreeSerializer(budget_tree).data
        return JsonResponse(json_data, status=200)

class SaveRuleSetWrapperView(APIView):

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=RuleSetWrapperSerializer,
        responses={
            200: SuccessfulOperationResponseSerializer,
            500: None,
            400: None
        })
    def post(self, request):
        try:
            body = request.body.decode('utf-8')
            serializer = RuleSetWrapperSerializer(data=json.loads(body))
            if serializer.is_valid():
                validated_data = serializer.validated_data
                users = validated_data.pop('users', None)
                rule_set_wrapper =RuleSetWrapperSerializer().create(validated_data)
                #rule_set_wrapper = RuleSetWrapper(**validated_data)
                if users:
                    rule_set_wrapper.users.set(users)
                get_rule_sets_service().save_rule_set(rule_set_wrapper)
                return JsonResponse(data=
                                    serialize_succesful_or_failed_operation_reponse(SuccessfulOperationResponse(
                                        message="Rule set wrapper saved successfully")), status=200)
            else:
                #bad request
                return JsonResponse({}, status=400)
        except Exception as e:
            return HttpResponseServerError()


class GetOrCreateRuleSetWrapperView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=GetOrCreateRuleSetWrapperSerializer,
        responses={
            200: RuleSetWrapperSerializer,
            500: None,
            400: None

        })
    def post(self, request):
        try:
            # data = json.loads(request.body.decode('utf-8'))
            user = request.user
            if not isinstance(user, CustomUser):
                raise ValueError(f"User must be an instance of CustomUser. Received {type(user)}")
            serializer = GetOrCreateRuleSetWrapperSerializer(data=request.data)
            if serializer.is_valid():
                dto: GetOrCreateRuleSetWrapper = GetOrCreateRuleSetWrapper(**serializer.validated_data)
                category_qualified_name = dto.category_qualified_name
                transaction_type = dto.type
                rule_set_wrapper = get_rule_sets_service().get_or_create_rule_set_wrapper(transaction_type, user,
                                                                                                  category_qualified_name)
                return JsonResponse(RuleSetWrapperSerializer(rule_set_wrapper).data, status=200)

            else:
                return JsonResponse({}, status=400)


        except Exception as e:
            traceback.print_exc()
            return JsonResponse({}, status=500)

class CategorizeTransactions(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=None,
        responses={
            200: CategorizeTransactionsResponseSerializer,
            500: None
        })
    def post(self, request):
        try:
            user = request.user
            if not isinstance(user, CustomUser):
                raise ValueError(f"User must be an instance of CustomUser. Received {type(user)}")
            response: CategorizeTransactionsResponse = get_transactions_service().categorise_transactions(user)
            return JsonResponse(CategorizeTransactionsResponseSerializer(response).data, status=200)
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({}, status=500)

class SaveAliasView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=SaveAliasSerializer,
        responses={
            200: {},
            500: None
        })
    def post(self, request):
        try:
            body = request.body.decode('utf-8')
            serializer = SaveAliasSerializer(data=json.loads(body))
            if serializer.is_valid():
                save_alias_dto= SaveAlias(**serializer.validated_data)
                alias = save_alias_dto.alias
                account_number = save_alias_dto.bank_account
                get_bank_accounts_service().save_alias(account_number, alias)
                return JsonResponse({}, status=200)
        except Exception as e:
            return JsonResponse({}, status=500)

class CategoryDetailsForPeriodView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=RevenueExpensesQueryWithCategorySerializer,
        responses={
            200: CategoryDetailsForPeriodHandlerResultSerializer,
            500: None,
            400: None

        })
    def post(self , request, *args, **kwargs):
        try:
            body = request.body.decode('utf-8')
            serializer = RevenueExpensesQueryWithCategorySerializer(data=json.loads(body))
            if serializer.is_valid(raise_exception=True):
                validated_data = serializer.validated_data
                query = RevenueExpensesQueryWithCategory(**validated_data)
                category = query.category
                result: CategoryDetailsForPeriodHandlerResult = get_analysis_service().get_category_details_for_period(
                    query, category)
                return JsonResponse(CategoryDetailsForPeriodHandlerResultSerializer(result).data, status=200)
            else:
                # bad request
                return JsonResponse({}, status=400)
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({}, status=500)

class CategoriesForAccountAndTransactionTypeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[BANK_ACCOUNT_NUMBER_PARAM, TRANSACTION_TYPE_PARAM],
        responses={
            200: STRING_LIST_RESPONSE,
            500: None
        })
    def get(self, request):
        try:
            account_number = request.query_params.get('bank_account')
            transaction_type = request.query_params.get("transaction_type")
            transaction_type = TransactionTypeEnum.from_value(transaction_type)
            bank_account_obj = get_bank_accounts_service().get_bank_account(account_number)
            result = Transaction.objects.find_distinct_categories_by_bank_account_and_type(bank_account_obj, transaction_type)
            return JsonResponse(list(result), safe=False, status=200)
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({}, status=500)


class PasswordResetAPIView(PasswordResetView):
    email_template_name = 'password_reset_email.html'  # Optional: Customize the email template

    @extend_schema(
        request=None,
        responses={
            200: inline_serializer(
                name='PasswordResetSuccessResponse',
                fields={'message': CharField()}
            ),
            400: inline_serializer(
                name='PasswordResetErrorResponse',
                fields={'error': CharField()}
            )
        }
    )
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            return JsonResponse({})
        return JsonResponse({"error": "Failed to send password reset email."}, status=400)

    def send_mail(self, subject_template_name, email_template_name, context, from_email, to_email,
                  html_email_template_name=None):
        """
        Custom email sending logic (optional).
        """
        message = render_to_string(email_template_name, context)
        email = EmailMessage(subject=context['subject'], body=message, from_email=from_email, to=[to_email])
        email.send()


class PasswordResetConfirmAPIView(PasswordResetConfirmView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            return JsonResponse({"message": "Password reset successful."})
        return JsonResponse({"error": "Failed to reset password."}, status=400)


class ValidateResetTokenAPIView(APIView):
    """
    Validate the UID and Token sent in the reset email.
    """

    @extend_schema(
        parameters=[
            OpenApiParameter(name='uidb64', type=str),
            OpenApiParameter(name='token', type=str)
        ],
        responses={
            200: inline_serializer(
                name='PasswordResetSuccessResponse',
                fields={'valid': BooleanField()}
            ),
            400: inline_serializer(
                name='PasswordResetErrorResponse',
                fields={'valid': BooleanField()}
            )
        }
    )

    def get(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
            if default_token_generator.check_token(user, token):
                return JsonResponse({"valid": True}, status=status.HTTP_200_OK)
            else:
                return JsonResponse({"valid": False}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return JsonResponse({"valid": False}, status=status.HTTP_400_BAD_REQUEST)


class DummyRuleView(APIView):

    @extend_schema(
        request=None,
        responses=RuleSerializer,
    )
    def get(self, request):
        pass
