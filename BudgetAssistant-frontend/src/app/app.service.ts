import {HttpClient, HttpEvent, HttpHeaders} from '@angular/common/http';
import {Injectable} from '@angular/core';
import {BehaviorSubject, catchError, map, Observable, of, Subject, tap, throwError} from 'rxjs';

import {Page, PageRequest} from "@daanvdn/ngx-pagination-data-source";
import {
    BudgetTrackerResult,
    CategoryDetailsForPeriodHandlerResult,
    CategoryMap,
    CategoryNode,
    CompositeTransactionsFileUploadResponse,
    DistributionByCategoryForPeriodHandlerResult2,
    FileWrapper,
    ResolvedStartEndDateShortcut,
    StartEndDateShortcut,
    TransactionsCategorizationResponse
} from './model';
import {AuthService} from "./auth/auth.service";
import {BudgetTreeNode, UpdateBudgetEntryResponse} from "./budget/budget.component";
import {
    ApiBudgetAssistantBackendClientService,
    BankAccount,
    GroupingEnum,
    PageTransactionsInContextRequest,
    PageTransactionsToManuallyReviewRequest,
    RevenueExpensesQuery, RuleSetWrapper,
    SimplifiedCategory,
    Transaction,
    TransactionQuery,
    TransactionTypeEnum,
    TypeEnum
} from "@daanvdn/budget-assistant-client";
import {environment} from "../environments/environment";
import {
    RevenueAndExpensesPerPeriodResponse
} from "@daanvdn/budget-assistant-client";
import {ExpensesAndRevenueForPeriod} from "@daanvdn/budget-assistant-client";
import {PageTransactionsRequest} from "@daanvdn/budget-assistant-client";
import {SortOrderEnum} from "@daanvdn/budget-assistant-client";
import {SortPropertyEnum} from "@daanvdn/budget-assistant-client";
import {TransactionsPage} from "@daanvdn/budget-assistant-client";
import {TransactionInContextQuery} from "@daanvdn/budget-assistant-client";
import {SuccessfulOperationResponse} from "@daanvdn/budget-assistant-client";
import {GetOrCreateRuleSetWrapper} from "@daanvdn/budget-assistant-client";


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
    private grouping$ = new BehaviorSubject<GroupingEnum | undefined>(undefined);
    selectedGrouping$ = this.grouping$.asObservable();
    private transactionType$ = new BehaviorSubject<TransactionTypeEnum | undefined>(undefined);
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
    public categoryMapSubject = new BehaviorSubject<CategoryMap | undefined >(undefined);
    public categoryMapObservable$ = this.categoryMapSubject.asObservable();



    private backendUrl = environment.API_BASE_PATH;

    constructor(private http: HttpClient, private authService: AuthService,
                private apiBudgetAssistantBackendClientService: ApiBudgetAssistantBackendClientService) {


        this.sharedCategoryTreeExpensesObservable$ = this.getSharedCategoryTreeExpensesObservable$();
        this.sharedCategoryTreeRevenueObservable$ = this.getSharedCategoryTreeRevenueObservable$();
        (async () => {
            let categoryNodes: CategoryNode[] = await this.getMergedCategoryTreeData();
            this.categoryMapSubject.next(new CategoryMap(categoryNodes));
            this.sharedCategoryTreeObservable$ = of(categoryNodes);
        })();


    }

    private getSharedCategoryTreeRevenueObservable$() {
        return this.apiBudgetAssistantBackendClientService.apiCategoryTreeRetrieve('REVENUE').pipe(
            map(categoryTree => {
                const nodes: CategoryNode[] = [];
                const rootNode = this.convertSimplifiedCategoryToCategoryNode(categoryTree.root, "REVENUE");
                nodes.push(...rootNode.children);
                return nodes;
            })
        );
    }

    private getSharedCategoryTreeExpensesObservable$() {
        return this.apiBudgetAssistantBackendClientService.apiCategoryTreeRetrieve('EXPENSES').pipe(
            map(categoryTree => {
                const nodes: CategoryNode[] = [];
                const rootNode = this.convertSimplifiedCategoryToCategoryNode(categoryTree.root, "EXPENSES");
                nodes.push(...rootNode.children);
                return nodes;
            })
        );
    }

    private convertSimplifiedCategoryToCategoryNode(simplified: SimplifiedCategory, type: TypeEnum): CategoryNode {
        const children: CategoryNode[] = simplified.children.map(childObj => {
            const [name, value] = Object.entries(childObj)[0];
            return this.convertSimplifiedCategoryToCategoryNode({
                name: name,
                qualifiedName: (value as unknown as SimplifiedCategory).qualifiedName,
                children: (value as unknown as SimplifiedCategory).children || [],
            id : (value as unknown as SimplifiedCategory).id
            }, type);
        });

        return {
            name: simplified.name,
            qualifiedName: simplified.qualifiedName,
            children: children,
            type: type, id : simplified.id
        };
    }


    private async getMergedCategoryTreeData(): Promise<CategoryNode[]> {

        let allData: CategoryNode[] = [];
        let expenses = await this.getSharedCategoryTreeExpensesObservable$().toPromise();
        let revenue = await this.getSharedCategoryTreeRevenueObservable$().toPromise();

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

    setTransactionType(transactionType: TransactionTypeEnum) {
        this.transactionType$.next(transactionType);
    }

    setGrouping(grouping: GroupingEnum) {
        this.grouping$.next(grouping);
    }


    public fetchBankAccountsForUser(): Observable<BankAccount[]> {


        this.apiBudgetAssistantBackendClientService.apiBankAccountsList().subscribe(result => {
            this.currentBankAccounts$.next(result);
        })


        return this.currentBankAccountsObservable$;


    }

    public countTransactionToManuallyReview(bankAccount: BankAccount): Observable<Number> {
        return this.apiBudgetAssistantBackendClientService.apiTransactionsCountTransactionsToManuallyReviewRetrieve(
            bankAccount.accountNumber).pipe(map(count => count.count));


    }


    public getRevenueAndExpensesByYear(restQuery: RevenueExpensesQuery): Observable<Page<ExpensesAndRevenueForPeriod>> {

        return this.apiBudgetAssistantBackendClientService.apiRevenueExpensesPerPeriodCreate(restQuery)
            .pipe(map((response: RevenueAndExpensesPerPeriodResponse) => {
                    let page: Page<ExpensesAndRevenueForPeriod> = {
                        content: response.content,
                        number: response.number,
                        size: response.size,
                        totalElements: response.totalElements

                    }
                    return page;


                }
            ));

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

    public saveTransaction(transaction: Transaction): void {

        this.apiBudgetAssistantBackendClientService.apiTransactionsSaveTransactionCreate(transaction).subscribe({
            next: () => {
            },
            error: (error) => console.error('Error saving transaction:', error)
        });



    }

    private camelToSnake(str: string): string {
        return str.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
    }

    private toPage(transactionsPage: TransactionsPage): Page<Transaction> {
        return {
            content: transactionsPage.content,
            number: transactionsPage.number,
            size: transactionsPage.size,
            totalElements: transactionsPage.totalElements
        };
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
        let pageTransactionsRequest: PageTransactionsRequest = {
            page: request.page,
            size: request.size,
            sortOrder: tmpSortOrder as SortOrderEnum,
            sortProperty: this.camelToSnake(tmpSortProperty) as SortPropertyEnum,
            query: transactionQuery

        }
        return this.apiBudgetAssistantBackendClientService.apiTransactionsPageTransactionsCreate(
            pageTransactionsRequest).pipe(map((result: TransactionsPage) => {

            return this.toPage(result);


        }));



    }

    public pageTransactionsInContext(request: PageRequest<Transaction>,
                                     query: TransactionInContextQuery): Observable<Page<Transaction>> {
        let tmpSortOrder = "asc";
        if (request.sort && request.sort.order) {
            tmpSortOrder = request.sort.order;
        }

        let tmpSortProperty = "bookingDate";
        if (request.sort && request.sort.property) {

            tmpSortProperty = request.sort.property;
        }
        let pageTransactionsInContextRequest: PageTransactionsInContextRequest = {
            page: request.page,
            size: request.size,
            sortOrder: tmpSortOrder as SortOrderEnum,
            sortProperty: this.camelToSnake(tmpSortProperty) as SortPropertyEnum,
            query: query

        }
        return this.apiBudgetAssistantBackendClientService.apiTransactionsPageTransactionsInContextCreate(
            pageTransactionsInContextRequest).pipe( map(result => {
            return this.toPage(result);
        }));
/*        let orig = this.http.get<Page<string>>(`${this.backendUrl}/page_transactions_in_context`, {params});
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

        }))*/
    }

    public pageTransactionsToManuallyReview(request: PageRequest<Transaction>,
                                            transactionType: TransactionTypeEnum): Observable<Page<Transaction>> {
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


        let pageTransactionsToManuallyReviewRequest : PageTransactionsToManuallyReviewRequest = {
            page: request.page,
            size: request.size,
            sortOrder: tmpSortOrder as SortOrderEnum,
            sortProperty: this.camelToSnake(tmpSortProperty) as SortPropertyEnum,
            bankAccount: bankAccount.accountNumber,
            transactionType: transactionType


        }
        return this.apiBudgetAssistantBackendClientService.apiTransactionsPageTransactionsToManuallyReviewCreate(pageTransactionsToManuallyReviewRequest).pipe(
            map(result => {
                return this.toPage(result);
            })

        );

        /*

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
*/

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


    public saveRuleSetWrapper(ruleSetWrapper: RuleSetWrapper): Observable<SuccessfulOperationResponse> {
        return this.apiBudgetAssistantBackendClientService.apiSaveRuleSetWrapperCreate(ruleSetWrapper)

    }

    public getOrCreateRuleSetWrapper(category: CategoryNode, categoryType: TypeEnum): Observable<RuleSetWrapper> {
        const getOrCreateRuleSetWrapper: GetOrCreateRuleSetWrapper = {
            categoryQualifiedName : category.qualifiedName,
            type:  categoryType,
        };
        return this.apiBudgetAssistantBackendClientService.apiGetOrCreateRuleSetWrapperCreate(getOrCreateRuleSetWrapper)

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

    public getCategoriesForAccountAndTransactionType(accountNumber: string, transactionType: TransactionTypeEnum): Observable<string[]>{

        const params = {
            accountNumber: accountNumber,
            transactionType: transactionType
        }
        return this.http.get<string[]>(
            `${this.backendUrl}/get_categories_for_account_and_transaction_type`, {params})

    }
}
