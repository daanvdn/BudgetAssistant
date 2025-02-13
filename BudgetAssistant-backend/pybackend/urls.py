"""pybackend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views
from .views import CustomLogoutView, DummyRuleView, PasswordResetAPIView, PasswordResetConfirmAPIView, RegisterView, \
    UpdateUserView, \
    ValidateResetTokenAPIView

from rest_framework.routers import DefaultRouter

router = DefaultRouter()
urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', admin.site.urls),
    path('api/bank-accounts/', views.BankAccountsForUserView.as_view(), name='bank_accounts_for_user'),
    path('api/revenue-expenses-per-period/', views.RevenueAndExpensesPerPeriodView.as_view(), name='revenue_and_expenses_per_period'),
    path('api/transactions/page-transactions/', views.PageTransactionsView.as_view(), name='page_transactions'),
    path('api/transactions/page-transactions-in-context/', views.PageTransactionsInContextView.as_view(), name='page_transactions_in_context'),
    path('api/transactions/page-transactions-to-manually-review/', views.PageTransactionsToManuallyReviewView.as_view(), name='page_transactions_to_manually_review'),
    path('api/transactions/count-transactions-to-manually-review/', views.CountTransactionsToManuallyReviewView.as_view(), name='count_transactions_to_manually_review'),
    path('api/transactions/save-transaction/', views.SaveTransactionView.as_view(), name='save_transaction'),
    path('api/transactions/upload-transactions/', views.UploadTransactionsView.as_view(), name='upload_transactions'),
    path('api/category-tree/', views.CategoryTreeView.as_view(), name='category_tree'),
    path('api/distinct-counterparty-names/', views.DistinctCounterpartyNamesView.as_view(), name='distinct_counterparty_names'),
    path('api/distinct-counterparty-accounts/', views.DistinctCounterpartyAccountsView.as_view(), name='distinct_counterparty_accounts'),
    path('api/analysis/revenue-expenses-per-period-and-category/', views.RevenueExpensesPerPeriodAndCategoryView.as_view(), name='revenue_expenses_per_period_and_category'),
    path('api/analysis/category-details-for-period/', views.CategoryDetailsForPeriodView.as_view(), name='category_details_for_period'),
    path('api/analysis/categories-for-account-and-transaction-type/', views.CategoriesForAccountAndTransactionTypeView.as_view(), name='categories_for_account_and_transaction_type'),
    #path('api/analysis/revenue-expenses-per-period-and-category-show-1-month-before-and-after/', views.revenue_expenses_per_period_and_category_show_1_month_before_and_after, name='revenue_expenses_per_period_and_category_show_1_month_before_and_after'),
    path('api/track-budget/', views.TrackBudgetView.as_view(), name='track_budget'),
    path('api/resolve-start-end-date-shortcut/', views.ResolveStartEndDateShortcutView.as_view(), name='resolve_start_end_date_shortcut'),
    path('api/update-budget-entry-amount/', views.UpdateBudgetEntryAmountView.as_view(), name='update_budget_entry_amount'),
    path('api/find-or-create-budget/', views.FindOrCreateBudgetView.as_view(), name='find_or_create_budget'),
    path('api/save-rule-set-wrapper/', views.SaveRuleSetWrapperView.as_view(), name='save_rule_set_wrapper'),
    path('api/get-or-create-rule-set-wrapper/', views.GetOrCreateRuleSetWrapperView.as_view(), name='get_or_create_rule_set_wrapper'),
    path('api/categorize-transactions/', views.CategorizeTransactions.as_view(), name='categorize_transactions'),
    path('api/save-alias/', views.SaveAliasView.as_view(), name='save_alias'),
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/update-user/', UpdateUserView.as_view(), name='update_user'),
    path('api/logout/', CustomLogoutView.as_view(), name='custom_logout'),
    path('api/password-reset/', PasswordResetAPIView.as_view(), name='password_reset'),
    path('api/password-reset-confirm/', PasswordResetConfirmAPIView.as_view(), name='password_reset_confirm'),
    path('api/password-reset-validate/<str:uidb64>/<str:token>/', ValidateResetTokenAPIView.as_view(), name='password_reset_validate'),
    path('api/dummy_view/', DummyRuleView.as_view(), name='dummy_rule_view'),


              ]+ router.urls
#router.register(r'transactions', TransactionViewSet, basename='transaction')


