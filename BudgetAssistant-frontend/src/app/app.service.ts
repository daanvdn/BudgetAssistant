import {HttpClient, HttpEvent, HttpHeaders} from '@angular/common/http';
import {Injectable} from '@angular/core';
import {BehaviorSubject, catchError, map, Observable, of, Subject, tap, throwError} from 'rxjs';

import {Page, PageRequest} from 'ngx-pagination-data-source';
import {CategoryNode, CategoryType} from './category-tree-dropdown/category-tree-dropdown.component';
import {
    BankAccount,
    BudgetTrackerResult,
    CategoryDetailsForPeriodHandlerResult,
    CompositeTransactionsFileUploadResponse,
    DistributionByCategoryForPeriodHandlerResult2,
    DistributionByTransactionTypeForPeriod,
    FileWrapper,
    Grouping,
    ResolvedStartEndDateShortcut,
    RevenueExpensesQuery,
    StartEndDateShortcut,
    Transaction,
    TransactionQuery,
    TransactionsCategorizationResponse, TransactionsInContextQuery,
    TransactionType
} from './model';
import {AuthService} from "./auth/auth.service";
import {BudgetTreeNode, UpdateBudgetEntryResponse} from "./budget/budget.component";
import {deserializeRuleSet, RuleSetWrapper} from "./query-builder/query-builder.interfaces";
import {environment} from "../environments/environment";


@Injectable({
    providedIn: 'root'
})
export class AppService {

    public DUMMY_BANK_ACCOUNT = "dummy";
    currentBankAccounts$ = new BehaviorSubject<BankAccount[]>([]);
    currentBankAccountsObservable$ = this.currentBankAccounts$.asObservable();
    private startDate$ = new BehaviorSubject<Date | undefined>(undefined);
    selectedStartDate$ = this.startDate$.asObservable();
    private endDate$ = new BehaviorSubject<Date |undefined>(undefined);
    selectedEndDate$ = this.endDate$.asObservable();
    private grouping$ = new BehaviorSubject<Grouping | undefined>(undefined);
    selectedGrouping$ = this.grouping$.asObservable();
    private transactionType$ = new BehaviorSubject<TransactionType |undefined>(undefined);
    public selectedTransactionType$ = this.transactionType$.asObservable();
    private expensesRecurrence$ = new BehaviorSubject<string  | undefined>(undefined);
    selectedExpensesRecurrence$ = this.expensesRecurrence$.asObservable();
    private revenueRecurrence$ = new BehaviorSubject<string |undefined>(undefined);
    selectedRevenueRecurrence$ = this.revenueRecurrence$.asObservable();
    private categoryQueryForSelectedPeriod$ = new BehaviorSubject<RevenueExpensesQuery |undefined>(undefined);
    public categoryQueryForSelectedPeriodObservable$ = this.categoryQueryForSelectedPeriod$.asObservable();

    public sharedCategoryTreeObservable$?: Observable<CategoryNode[]>;
    public sharedCategoryTreeExpensesObservable$: Observable<CategoryNode[]>;
    public sharedCategoryTreeRevenueObservable$: Observable<CategoryNode[]>;
    public fileUploadComplete$ = new Subject<void>();
    public selectedBankAccount$ = new BehaviorSubject<BankAccount | undefined>(undefined);
    public selectedBankAccountObservable$ = this.selectedBankAccount$.asObservable();

    private backendUrl = environment.backendUrl;

    constructor(private http: HttpClient, private authService: AuthService) {


        this.sharedCategoryTreeExpensesObservable$ = this.http.get<CategoryNode[]>(
            `${this.backendUrl}/category_tree_expenses`, {})
            .pipe(map(nodes => {
                //remove nodes with name "DUMMY CATEGORY" or "NO CATEGORY"
                nodes = nodes.filter(node => !(node.name === "NO CATEGORY" || node.name === "DUMMY CATEGORY"));
                return this.setCategoryType(nodes, "EXPENSES");
            }));

        this.sharedCategoryTreeRevenueObservable$ = this.http.get<CategoryNode[]>(
            `${this.backendUrl}/category_tree_revenue`, {})
            .pipe(map(revenueNodes => {
                //remove nodes with name "DUMMY CATEGORY" or "NO CATEGORY"
                revenueNodes = revenueNodes.filter(
                    node => !(node.name === "NO CATEGORY" || node.name === "DUMMY CATEGORY"));
                return this.setCategoryType(revenueNodes, "REVENUE");
            }));

        (async () => {
            let categoryNodes: CategoryNode[] = await this.getMergedCategoryTreeData();
            this.sharedCategoryTreeObservable$ = of(categoryNodes);
        })();


    }


    private async getMergedCategoryTreeData(): Promise<CategoryNode[]> {

        function setCategoryType(nodes: CategoryNode[], value: CategoryType): CategoryNode[] {
            nodes.forEach(node => {
                node.type = value;
                if (node.children) {
                    setCategoryType(node.children, value);
                }
            });
            return nodes;
        }

        let allData: CategoryNode[] = [];
        let expenses = await this.http.get<CategoryNode[]>(`${this.backendUrl}/category_tree_expenses`, {})
            .pipe(map(nodes => {
                return setCategoryType(nodes, "EXPENSES");
            })).toPromise();

        let revenue = await this.http.get<CategoryNode[]>(`${this.backendUrl}/category_tree_revenue`, {})
            .pipe(map(revenueNodes => {
                return setCategoryType(revenueNodes, "REVENUE");
            })).toPromise();
        if (expenses == undefined || revenue == undefined) {
            throw new Error("expenses or revenue is undefined!");
        }

        allData = allData.concat(expenses);
        for (const categoryNode of revenue) {
            if (!(categoryNode.name === "NO CATEGORY" || categoryNode.name === "DUMMY CATEGORY")) {
                allData.push(categoryNode);
            }

        }
        return allData;


    }


    private setCategoryType(nodes: CategoryNode[], value: CategoryType): CategoryNode[] {
        nodes.forEach(node => {
            node.type = value;
            if (node.children) {
                this.setCategoryType(node.children, value);
            }
        });
        return nodes;
    }


    setBankAccount(bankAccount: BankAccount) {
        this.selectedBankAccount$.next(bankAccount);
    }


    setCategoryQueryForSelectedPeriod$(query: RevenueExpensesQuery) {
        this.categoryQueryForSelectedPeriod$.next(query);
    }


    setStartAndEndDate(start: Date, end: Date) {
        this.startDate$.next(start);
        this.endDate$.next(end);

    }


    setExpensesRecurrence(selectedType: string) {
        this.expensesRecurrence$.next(selectedType)
    }

    setRevenueRecurrence(selectedType: string) {
        this.revenueRecurrence$.next(selectedType)
    }

    setTransactionType(transactionType: TransactionType) {
        this.transactionType$.next(transactionType);
    }

    setGrouping(grouping: Grouping) {
        this.grouping$.next(grouping);
    }


    public fetchBankAccountsForUser(): Observable<BankAccount[]> {

        let user = this.authService.getUser();
        if (!user || !user.userName) {
            throw new Error("User is not defined!");
        }

        const params = {
            userName: user.userName

        }
        this.http.get<BankAccount[]>(`${this.backendUrl}/bank_accounts_for_user`, {params}).subscribe(result => {
            let accounts = result.map(ba => {
                let copy = {...ba};
                if (!copy.alias) {
                    copy.alias = null;
                }
                copy.editAlias = false;

                return copy;
            })
            this.currentBankAccounts$.next(accounts)
        });

        return this.currentBankAccountsObservable$;


    }

    public countTransactionToManuallyReview(bankAccount: BankAccount): Observable<Number> {
        const params = {
            bankAccount: bankAccount.accountNumber
        }
        let result = this.http.get<Number>(
            `${this.backendUrl}/count_transactions_to_manually_review`, {params})
        return result;


    }


    public getRevenueAndExpensesByYear(restQuery: RevenueExpensesQuery): Observable<Page<DistributionByTransactionTypeForPeriod>> {

        const params = {
            query: JSON.stringify(restQuery),
            responseType: "json"

        }

        let result = this.http.get<Page<DistributionByTransactionTypeForPeriod>>(
            `${this.backendUrl}/revenue_and_expenses_by_year`, {params})
        return result;


    }

    private parseDate(json: string): Date {
        let parts: string[] = json.split('-');
        let day: number = parseInt(parts[0])
        let month: number = parseInt(parts[1])
        let year: number = parseInt(parts[2])
        let dateObj = new Date();
        dateObj.setDate(day);
        dateObj.setMonth(month);
        dateObj.setFullYear(year);


        return dateObj;

    }

    public saveTransaction(transaction: Transaction) {

        let copy: Transaction = {

            transaction_id: transaction.transaction_id,
            bankAccount: null,
            bookingDate: null,
            statementNumber: null,
            transactionNumber: null,
            counterparty: null,
            transaction: null,
            currencyDate: null,
            amount: null,
            currency: null,
            bic: null,
            countryCode: null,
            communications: null,
            category: transaction.category,
            isRecurring: transaction.isRecurring,
            isAdvanceSharedAccount: transaction.isAdvanceSharedAccount,
            manuallyAssignedCategory: null,
            isManuallyReviewed: null
        };

        let transactionJsonVar: string = JSON.stringify(copy)
        const headers = new HttpHeaders().set('Content-Type', 'application/json; charset=utf-8');
        const options = {headers: headers};

        let result = this.http.post<string>(`${this.backendUrl}/save_transaction`, transactionJsonVar, options)
        result.subscribe(); //fixme: pass result to caller


    }

    public pageTransactions(request: PageRequest<Transaction>,
                            transactionQuery: TransactionQuery | undefined): Observable<Page<Transaction>> {
        let tmpSortOrder = "asc";
        if (request.sort && request.sort.order) {
            tmpSortOrder = request.sort.order;
        }

        let tmpSortProperty = "bookingDate";
        if (request.sort && request.sort.property) {

            tmpSortProperty = request.sort.property;
        }
        let params;
        if (transactionQuery == null) {
            params = {
                page: request.page,
                size: request.size,
                sortOrder: tmpSortOrder,
                sortProperty: tmpSortProperty,
                responseType: "json"
            }
        }
        else {
            params = {
                page: request.page,
                size: request.size,
                sortOrder: tmpSortOrder,
                sortProperty: tmpSortProperty,
                query: JSON.stringify(transactionQuery),
                responseType: "json"
            }
        }


        let orig = this.http.get<Page<string>>(`${this.backendUrl}/page_transactions`, {params})

        return orig.pipe(map(p => {

            let newContent: Transaction[] = p.content.map(t => JSON.parse(t, (k, v) => {

                if (k == "bookingDate" || k == "currencyDate") {
                    return this.parseDate(v)
                }
                else {
                    return v;
                }

            }))


            let newPage: Page<Transaction> = {
                content: newContent, number: p.number, size: p.size, totalElements: p.totalElements

            }

            return newPage;

        }))


    }

    public pageTransactionsInContext(request: PageRequest<Transaction>, query: TransactionsInContextQuery): Observable<Page<Transaction>>{
        let tmpSortOrder = "asc";
        if (request.sort && request.sort.order) {
            tmpSortOrder = request.sort.order;
        }

        let tmpSortProperty = "bookingDate";
        if (request.sort && request.sort.property) {

            tmpSortProperty = request.sort.property;
        }
        let params = {
            page: request.page,
            size: request.size,
            sortOrder: tmpSortOrder,
            sortProperty: tmpSortProperty,
            query: JSON.stringify(query),
            responseType: "json"
        }

        let orig = this.http.get<Page<string>>(`${this.backendUrl}/page_transactions_in_context`, {params});
        return orig.pipe(map(p => {

            let newContent: Transaction[] = p.content.map(t => JSON.parse(t, (k, v) => {

                if (k == "bookingDate" || k == "currencyDate") {
                    return this.parseDate(v)
                }
                else {
                    return v;
                }

            }))


            let newPage: Page<Transaction> = {
                content: newContent, number: p.number, size: p.size, totalElements: p.totalElements

            }

            return newPage;

        }))
    }

    public pageTransactionsToManuallyReview(request: PageRequest<Transaction>,
                                            transactionType: TransactionType): Observable<Page<Transaction>> {
        let bankAccount = this.selectedBankAccount$.getValue();
        if (bankAccount == null) {
            throw new Error("Bank account is not defined!");
        }
        let tmpSortOrder = "asc";
        if (request.sort && request.sort.order) {
            tmpSortOrder = request.sort.order;
        }

        let tmpSortProperty = "counterparty";
        if (request.sort && request.sort.property) {

            tmpSortProperty = request.sort.property;
        }

        let params = {
            page: request.page,
            size: request.size,
            sortOrder: tmpSortOrder,
            sortProperty: tmpSortProperty,
            bankAccount: bankAccount.accountNumber,
            transactionType: transactionType,
            responseType: "json"
        }
        let orig = this.http.get<Page<string>>(`${this.backendUrl}/page_transactions_to_manually_review`, {params});

        return orig.pipe(map(p => {

            let newContent: Transaction[] = p.content.map(t => JSON.parse(t, (k, v) => {

                if (k == "bookingDate" || k == "currencyDate") {
                    return this.parseDate(v)
                }
                else {
                    return v;
                }

            }))


            let newPage: Page<Transaction> = {
                content: newContent, number: p.number, size: p.size, totalElements: p.totalElements

            }

            return newPage;

        }))


    }

    public getRevenueExpensesPerPeriodAndCategory(restQuery: RevenueExpensesQuery): Observable<DistributionByCategoryForPeriodHandlerResult2> {


        const params = {
            query: JSON.stringify(restQuery), responseType: "json"

        }
        return this.http.get<DistributionByCategoryForPeriodHandlerResult2>(
            `${this.backendUrl}/revenue_expenses_per_period_and_category`, {params})

    }

    public trackBudget(restQuery: RevenueExpensesQuery): Observable<BudgetTrackerResult> {
        const params = {
            query: JSON.stringify(restQuery), responseType: "json"
        }
        return this.http.get<BudgetTrackerResult>(`${this.backendUrl}/track_budget`, {params}).pipe(
            catchError(error => {
                console.error('Error occurred:', error);
                return throwError(error);
            })
        );
    }


    public getRevenueExpensesPerPeriodAndCategoryShow1MonthBeforeAndAfter(restQuery: RevenueExpensesQuery): Observable<DistributionByCategoryForPeriodHandlerResult2> {


        const params = {
            query: JSON.stringify(restQuery), responseType: "json"

        }
        return this.http.get<DistributionByCategoryForPeriodHandlerResult2>(
            `${this.backendUrl}/revenue_expenses_per_period_and_category_show_1_month_before_and_after`, {params})

    }


    public resolveStartEndDateShortcut(startEnDateShortCut: StartEndDateShortcut): Observable<ResolvedStartEndDateShortcut> {

        const params = {
            "query": startEnDateShortCut
        }
        return this.http.get<ResolvedStartEndDateShortcut>(`${this.backendUrl}/resolve_start_end_date_shortcut`,
            {params})

    }


    public getDistinctCounterpartyNames(bankAccount: string): Observable<string[]> {
        const params = {
            account: bankAccount
        }
        return this.http.get<string[]>(`${this.backendUrl}/distinct_counterparty_names`, {params})
    }

    public getDistinctCounterpartyAccounts(bankAccount: string): Observable<string[]> {
        const params = {
            account: bankAccount
        }
        return this.http.get<string[]>(`${this.backendUrl}/distinct_counterparty_accounts`, {params})
    }

    public uploadTransactionFiles(fileWrappers: FileWrapper[],
                                  userName: string): Observable<HttpEvent<CompositeTransactionsFileUploadResponse>> {

        // Create a FormData instance
        let formData = new FormData();


        for (const fileWrapper of fileWrappers) {
            fileWrapper.inProgress = true;
            formData.append("files", fileWrapper.file, fileWrapper.file.name);
        }
        formData.append("userName", userName);


        return this.http.post<CompositeTransactionsFileUploadResponse>(`${this.backendUrl}/upload_transactions`,
            formData, {
                reportProgress: true, observe: 'events'
            }).pipe(tap(() => {
            this.fetchBankAccountsForUser(); //fixme: need for subscription?
            this.fileUploadComplete$.next();
        }));

    }

    public findOrCreateBudget(bankAccount: BankAccount): Observable<BudgetTreeNode[]> {

        const params = {
            account: bankAccount.accountNumber
        }
        return this.http.get<BudgetTreeNode[]>(`${this.backendUrl}/find_or_create_budget`, {params})


    }

    public updateBudgetEntryAmount(budgetEntry: BudgetTreeNode): Observable<UpdateBudgetEntryResponse> {

        const headers = new HttpHeaders().set('Content-Type', 'application/json; charset=utf-8');
        const options = {headers: headers};

        const body = JSON.stringify(budgetEntry);


        return this.http.post<UpdateBudgetEntryResponse>(`${this.backendUrl}/update_budget_entry_amount`, body, options)


    }


    public saveRuleSetWrapper(ruleSetWrapper: RuleSetWrapper): Observable<void> {


        const headers = new HttpHeaders().set('Content-Type', 'application/json; charset=utf-8');
        const options = {headers: headers};

        let body = {
            ruleSet: ruleSetWrapper.ruleSet.toJson(),
            category: ruleSetWrapper.category,
            categoryType: ruleSetWrapper.categoryType,
            id: ruleSetWrapper.id,
            users: ruleSetWrapper.users,


        }

        let result = this.http.post<void>(`${this.backendUrl}/save_rule_set_wrapper`, body, options)
        return result;
    }

    public getOrCreateRuleSetWrapper(category: CategoryNode, categoryType: CategoryType,
                                     userName: string): Observable<RuleSetWrapper> {
        const params = {
            type: categoryType, userName: userName, category: category.qualifiedName
        }
        return this.http.get<Record<string, any>>(`${this.backendUrl}/get_or_create_rule_set_wrapper`, {params})
            .pipe(map(response => {

                let id = response['id'];
                let category = response["category"];
                let categoryType = response["categoryType"];
                let users = response["users"];
                let ruleSet = JSON.stringify(response["ruleSet"]);

                let wrapper: RuleSetWrapper = {
                    id: id,
                    category: category,
                    ruleSet: deserializeRuleSet(ruleSet),
                    categoryType: categoryType,
                    users: users
                }
                return wrapper;

            }));

    }

    public categorizeTransactions(userName: string): Observable<TransactionsCategorizationResponse> {

        const params = {
            userName: userName
        }
        return this.http.get<TransactionsCategorizationResponse>(`${this.backendUrl}/categorize_transactions`,
            {params});

    }

    public saveBankAccountAlias(bankAccount: BankAccount): Observable<void> {
        const headers = new HttpHeaders().set('Content-Type', 'application/json; charset=utf-8');
        const options = {headers: headers};

        const body = {
            alias: bankAccount.alias, accountNumber: bankAccount.accountNumber
        };
        return this.http.post<void>(`${this.backendUrl}/save_bankacount_alias`, body, options)
    }

    public getCategoryDetailsForPeriod(revenueExpensesQuery: RevenueExpensesQuery, category:string): Observable<CategoryDetailsForPeriodHandlerResult>{
        const params = {
            query: JSON.stringify(revenueExpensesQuery),
            category: category,
            responseType: "json"

        }
        return this.http.get<CategoryDetailsForPeriodHandlerResult>(
            `${this.backendUrl}/get_category_details_for_period`, {params})
    }

    public getCategoriesForAccountAndTransactionType(accountNumber: string, transactionType: TransactionType): Observable<string[]>{

        const params = {
            accountNumber: accountNumber,
            transactionType: transactionType
        }
        return this.http.get<string[]>(
            `${this.backendUrl}/get_categories_for_account_and_transaction_type`, {params})

    }
}



