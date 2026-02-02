import {HttpClient, HttpEvent, HttpResponse} from '@angular/common/http';
import {Injectable} from '@angular/core';
import {BehaviorSubject, map, Observable, of, Subject, tap} from 'rxjs';

import {Page, PageRequest} from "ngx-pagination-data-source";
import {
    CategoryMap,
    DistributionByCategoryForPeriodHandlerResult2,
    FileWrapper,
    ResolvedStartEndDateShortcut,
    StartEndDateShortcut,
    TransactionsCategorizationResponse
} from './model';
import {AuthService} from "./auth/auth.service";
import {BudgetTreeNode} from "./budget/budget.component";
import {
    BankAccountRead,
    BudgetAssistantApiService,
    BudgetTreeCreate,
    BudgetTreeNodeRead,
    BudgetTreeNodeUpdate,
    BudgetTreeRead,
    CategoriesForAccountResponse,
    CategorizeTransactionsResponse,
    CategoryDetailsForPeriodResponse,
    CategoryRead,
    CategoryTreeRead,
    DateRangeShortcut,
    ExpensesAndRevenueForPeriod,
    GetOrCreateRuleSetWrapperRequest,
    Grouping,
    PageTransactionsInContextRequest,
    PageTransactionsRequest,
    PageTransactionsToManuallyReviewRequest,
    PaginatedResponseTransactionRead,
    ResolvedDateRange,
    RevenueAndExpensesPerPeriodResponse,
    RevenueExpensesQuery,
    RevenueExpensesQueryWithCategory,
    RuleSetWrapperCreate,
    RuleSetWrapperRead,
    SaveAliasRequest,
    SortOrder,
    SuccessResponse,
    TransactionInContextQuery,
    TransactionQuery,
    TransactionRead,
    TransactionSortProperty,
    TransactionTypeEnum,
    TransactionUpdate,
    UploadTransactionsResponse
} from "@daanvdn/budget-assistant-client";
import {environment} from "../environments/environment";


@Injectable({
    providedIn: 'root'
})
export class AppService {

    public DUMMY_BANK_ACCOUNT = "dummy";
    currentBankAccounts$ = new BehaviorSubject<BankAccountRead[]>([]);
    currentBankAccountsObservable$ = this.currentBankAccounts$.asObservable();
    private startDate$ = new BehaviorSubject<Date | undefined>(undefined);
    selectedStartDate$ = this.startDate$.asObservable();
    private endDate$ = new BehaviorSubject<Date | undefined>(undefined);
    selectedEndDate$ = this.endDate$.asObservable();
    private grouping$ = new BehaviorSubject<Grouping | undefined>(undefined);
    selectedGrouping$ = this.grouping$.asObservable();
    private transactionType$ = new BehaviorSubject<TransactionTypeEnum | undefined>(undefined);
    public selectedTransactionType$ = this.transactionType$.asObservable();
    private expensesRecurrence$ = new BehaviorSubject<string | undefined>(undefined);
    selectedExpensesRecurrence$ = this.expensesRecurrence$.asObservable();
    private revenueRecurrence$ = new BehaviorSubject<string | undefined>(undefined);
    selectedRevenueRecurrence$ = this.revenueRecurrence$.asObservable();
    private categoryQueryForSelectedPeriod$ = new BehaviorSubject<RevenueExpensesQuery | undefined>(undefined);
    public categoryQueryForSelectedPeriodObservable$ = this.categoryQueryForSelectedPeriod$.asObservable();

    public sharedCategoryTreeObservable$: Observable<CategoryRead[]> = of([]);
    public sharedCategoryTreeExpensesObservable$: Observable<CategoryRead[]>;
    public sharedCategoryTreeRevenueObservable$: Observable<CategoryRead[]>;
    public fileUploadComplete$ = new Subject<void>();
    public selectedBankAccount$ = new BehaviorSubject<BankAccountRead | undefined>(undefined);
    public selectedBankAccountObservable$ = this.selectedBankAccount$.asObservable();
    public categoryMapSubject = new BehaviorSubject<CategoryMap | undefined>(undefined);
    public categoryMapObservable$ = this.categoryMapSubject.asObservable();
    refreshBankAccounts = new BehaviorSubject<boolean | undefined>(undefined);
    refreshBankAccountsObservable$ = this.refreshBankAccounts.asObservable();


    private backendUrl = environment.API_BASE_PATH;

    constructor(private http: HttpClient, private authService: AuthService,
                private apiService: BudgetAssistantApiService) {


        this.sharedCategoryTreeExpensesObservable$ = this.getSharedCategoryTreeExpensesObservable$();
        this.sharedCategoryTreeRevenueObservable$ = this.getSharedCategoryTreeRevenueObservable$();
        (async () => {
            let categories: CategoryRead[] = await this.getMergedCategoryTreeData();
            this.categoryMapSubject.next(new CategoryMap(categories));
            this.sharedCategoryTreeObservable$ = of(categories);
        })();


    }

    public triggerRefreshBankAccounts() {
        this.refreshBankAccounts.next(true);
    }


    private getSharedCategoryTreeRevenueObservable$() {
        return this.apiService.categories.getCategoryTreeApiCategoriesTreeGet(TransactionTypeEnum.REVENUE).pipe(
            map((categoryTree: CategoryTreeRead) => {
                let childrenCast: Array<CategoryRead> = []
                let children = categoryTree.root?.children;
                if (children) {
                    for (let childObj of children) {
                        childrenCast.push(childObj as CategoryRead);
                    }
                }
                return childrenCast;

            })
        );
    }

    private getSharedCategoryTreeExpensesObservable$(): Observable<CategoryRead[]> {
        return this.apiService.categories.getCategoryTreeApiCategoriesTreeGet(TransactionTypeEnum.EXPENSES).pipe(
            map((categoryTree: CategoryTreeRead) => {
                let childrenCast: Array<CategoryRead> = []
                let children = categoryTree.root?.children;
                if (children) {
                    for (let childObj of children) {
                        childrenCast.push(childObj as CategoryRead);
                    }
                }
                return childrenCast;

            })
        );
    }

    // The convertSimplifiedCategoryToCategoryNode method has been removed as we now use SimplifiedCategory directly


    private async getMergedCategoryTreeData(): Promise<CategoryRead[]> {

        let allData: CategoryRead[] = [];
        let expenses = await this.getSharedCategoryTreeExpensesObservable$().toPromise();
        let revenue = await this.getSharedCategoryTreeRevenueObservable$().toPromise();

        if (expenses == undefined || revenue == undefined) {
            throw new Error("expenses or revenue is undefined!");
        }

        allData = allData.concat(expenses);
        for (const category of revenue) {
            if (!(category.name === "NO CATEGORY" || category.name === "DUMMY CATEGORY")) {
                allData.push(category);
            }
        }
        return allData;
    }

    setBankAccount(bankAccount: BankAccountRead) {
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

    setGrouping(grouping: Grouping) {
        this.grouping$.next(grouping);
    }


    public fetchBankAccountsForUser(): Observable<BankAccountRead[]> {


        return this.apiService.bankAccounts.getBankAccountsForUserApiBankAccountsGet();


    }

    public countTransactionToManuallyReview(bankAccountNumber: string): Observable<Number> {
        if (!bankAccountNumber) {
            console.error('Bank account number is undefined');
            return of(0); // Return observable with 0 if bankAccount or accountNumber is undefined
        }
        return this.apiService.transactions.countTransactionsToManuallyReviewApiTransactionsCountToManuallyReviewGet(
            bankAccountNumber).pipe(map(count => count.count));


    }


    public getRevenueAndExpensesByYear(restQuery: RevenueExpensesQuery): Observable<Page<ExpensesAndRevenueForPeriod>> {

        return this.apiService.analysis.getRevenueAndExpensesPerPeriodApiAnalysisRevenueExpensesPerPeriodPost(restQuery)
            .pipe(map((response: RevenueAndExpensesPerPeriodResponse) => {
                    let page: Page<ExpensesAndRevenueForPeriod> = {
                        content: response.content,
                        number: response.page ?? 0,
                        size: response.size ?? response.content.length,
                        totalElements: response.totalElements ?? response.content.length

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

    public saveTransaction(transaction: TransactionRead): void {
        const transactionUpdate: TransactionUpdate = {
            transaction: transaction.transaction,
            categoryId: transaction.categoryId,
            manuallyAssignedCategory: transaction.manuallyAssignedCategory,
            isRecurring: transaction.isRecurring,
            isAdvanceSharedAccount: transaction.isAdvanceSharedAccount,
            isManuallyReviewed: transaction.isManuallyReviewed
        };
        this.apiService.transactions.saveTransactionApiTransactionsSavePost(transaction.transactionId,
            transactionUpdate).subscribe({
            next: () => {
            },
            error: (error) => console.error('Error saving transaction:', error)
        });


    }

    private camelToSnake(str: string): string {
        return str.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
    }

    private toPage(paginatedResponse: PaginatedResponseTransactionRead): Page<TransactionRead> {
        // Note: The new API returns 0-indexed pages
        let page = {
            content: paginatedResponse.content,
            number: paginatedResponse.page,
            size: paginatedResponse.size,
            totalElements: paginatedResponse.totalElements
        };
        return page;
    }

    public pageTransactions(request: PageRequest<TransactionRead>,
                            transactionQuery: TransactionQuery | undefined): Observable<Page<TransactionRead>> {
        //request.size = 1000;

        let tmpSortOrder = "asc";
        if (request.sort && request.sort.order) {
            tmpSortOrder = request.sort.order;
        }

        let tmpSortProperty = "bookingDate";
        if (request.sort && request.sort.property) {

            tmpSortProperty = request.sort.property;
        }
        let pageTransactionsRequest: PageTransactionsRequest = {
            page: request.page + 1,
            size: request.size,
            sortOrder: tmpSortOrder as SortOrder,
            sortProperty: this.camelToSnake(tmpSortProperty) as TransactionSortProperty,
            query: transactionQuery

        }
        return this.apiService.transactions.pageTransactionsApiTransactionsPagePost(
            pageTransactionsRequest).pipe(map((result: PaginatedResponseTransactionRead) => {

            return this.toPage(result);


        }));


    }

    public pageTransactionsInContext(request: PageRequest<TransactionRead>,
                                     query: TransactionInContextQuery): Observable<Page<TransactionRead>> {
        let tmpSortOrder = "asc";
        if (request.sort && request.sort.order) {
            tmpSortOrder = request.sort.order;
        }

        let tmpSortProperty = "bookingDate";
        if (request.sort && request.sort.property) {

            tmpSortProperty = request.sort.property;
        }
        let pageTransactionsInContextRequest: PageTransactionsInContextRequest = {
            page: request.page++,
            size: request.size,
            sortOrder: tmpSortOrder as SortOrder,
            sortProperty: this.camelToSnake(tmpSortProperty) as TransactionSortProperty,
            query: query

        }
        return this.apiService.transactions.pageTransactionsInContextApiTransactionsPageInContextPost(
            pageTransactionsInContextRequest).pipe(map(result => {
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

    public pageTransactionsToManuallyReview(request: PageRequest<TransactionRead>,
                                            transactionType: TransactionTypeEnum): Observable<Page<TransactionRead>> {
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


        let pageTransactionsToManuallyReviewRequest: PageTransactionsToManuallyReviewRequest = {
            page: request.page++,
            size: request.size,
            sortOrder: tmpSortOrder as SortOrder,
            sortProperty: this.camelToSnake(tmpSortProperty) as TransactionSortProperty,
            bankAccount: bankAccount.accountNumber,
            transactionType: transactionType


        }
        return this.apiService.transactions.pageTransactionsToManuallyReviewApiTransactionsPageToManuallyReviewPost(
            pageTransactionsToManuallyReviewRequest).pipe(
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


    public getRevenueExpensesPerPeriodAndCategoryShow1MonthBeforeAndAfter(restQuery: RevenueExpensesQuery): Observable<DistributionByCategoryForPeriodHandlerResult2> {


        const params = {
            query: JSON.stringify(restQuery), responseType: "json"

        }

        return this.http.get<DistributionByCategoryForPeriodHandlerResult2>(
            `${this.backendUrl}/revenue_expenses_per_period_and_category_show_1_month_before_and_after`, {params})

    }


    public resolveStartEndDateShortcut(startEnDateShortCut: StartEndDateShortcut): Observable<ResolvedStartEndDateShortcut> {
        return this.apiService.analysis.resolveStartEndDateShortcutApiAnalysisResolveDateShortcutGet(
            startEnDateShortCut as DateRangeShortcut)
            .pipe(map((resolvedDateRange: ResolvedDateRange) => {
                //parse the ResolvedDateRange.start string and ResolvedDateRange.end string
                // to Date and return a new ResolvedStartEndDateShortcut object
                let start: Date = this.parseDate(resolvedDateRange.start);
                let end: Date = this.parseDate(resolvedDateRange.end);
                return new ResolvedStartEndDateShortcut(start, end);

            }));

    }


    public getDistinctCounterpartyNames(bankAccount: string): Observable<Array<string>> {

        return this.apiService.transactions.getDistinctCounterpartyNamesApiTransactionsDistinctCounterpartyNamesGet(
            bankAccount) as Observable<Array<string>>;
    }

    public getDistinctCounterpartyAccounts(bankAccount: string): Observable<Array<string>> {
        return this.apiService.transactions.getDistinctCounterpartyAccountsApiTransactionsDistinctCounterpartyAccountsGet(
            bankAccount) as Observable<Array<string>>;
    }

    public uploadTransactionFiles(fileWrappers: FileWrapper[],
                                  userName: string): Observable<HttpEvent<UploadTransactionsResponse>> {


        // Mark files as in progress
        const files: Blob[] = [];
        for (const fileWrapper of fileWrappers) {
            fileWrapper.inProgress = true;
            files.push(fileWrapper.file);
        }

        // Call the API client service method
        return this.apiService.transactions.uploadTransactionsApiTransactionsUploadPost(
            files,
            'events',
            true
        ).pipe(tap(() => {
            this.fileUploadComplete$.next();
        })) as Observable<HttpEvent<UploadTransactionsResponse>>;

    }

    public findOrCreateBudget(bankAccount: BankAccountRead): Observable<BudgetTreeNode[]> {

        const budgetTreeCreate: BudgetTreeCreate = {
            bankAccountId: bankAccount.accountNumber
        }
        let obs: Observable<BudgetTreeRead> = this.apiService.budget.findOrCreateBudgetApiBudgetFindOrCreatePost(
            budgetTreeCreate);
        return obs.pipe(map((budgetTree: BudgetTreeRead) => {
            // Convert the BudgetTree to an array of BudgetTreeNode objects
            const result: BudgetTreeNode[] = [];

            // Process the root node and its children recursively
            if (budgetTree.root) {
                this.convertBudgetTreeNodeApiToBudgetTreeNode(budgetTree.root, -1, result);
            }

            return result;
        }));

    }

    private convertBudgetTreeNodeApiToBudgetTreeNode(apiNode: BudgetTreeNodeRead, parentId: number,
                                                     result: BudgetTreeNode[]): void {
        // Create a new BudgetTreeNode from the API node
        const localNode: BudgetTreeNode = {
            budgetTreeNodeAmount: apiNode.amount,
            budgetTreeNodeId: apiNode.id,
            budgetTreeNodeParentId: parentId,
            children: [],
            name: apiNode.name ?? '',
            qualifiedName: apiNode.qualifiedName ?? ''
        };

        // Add the node to the result array
        result.push(localNode);

        // Process children recursively
        if (apiNode.children && apiNode.children.length > 0) {
            for (const childNode of apiNode.children) {
                // Process the child node recursively
                this.convertBudgetTreeNodeApiToBudgetTreeNode(childNode, localNode.budgetTreeNodeId, result);

                // Add the converted child to the current node's children array
                localNode.children.push(result[result.length - 1]);
            }
        }
    }

    private convertBudgetTreeNodeToBudgetTreeNodeApi(node: BudgetTreeNode): BudgetTreeNodeRead {

        return {
            amount: node.budgetTreeNodeAmount,
            id: node.budgetTreeNodeId,
            children: node.children.map(child => this.convertBudgetTreeNodeToBudgetTreeNodeApi(child)),
            name: node.name,
            qualifiedName: node.qualifiedName
        }
    }


    public updateBudgetEntryAmount(budgetEntry: BudgetTreeNode): Observable<HttpResponse<any>> {
        const budgetTreeNodeUpdate: BudgetTreeNodeUpdate = {
            amount: budgetEntry.budgetTreeNodeAmount
        };
        return this.apiService.budget.updateBudgetEntryAmountApiBudgetEntryNodeIdPatch(
            budgetEntry.budgetTreeNodeId, budgetTreeNodeUpdate, 'response')

    }


    public saveRuleSetWrapper(ruleSetWrapper: RuleSetWrapperRead): Observable<SuccessResponse> {
        if (!ruleSetWrapper.categoryId) {
            throw new Error("categoryId is required to save a RuleSetWrapper");
        }
        const ruleSetWrapperCreate: RuleSetWrapperCreate = {
            categoryId: ruleSetWrapper.categoryId,
            ruleSet: ruleSetWrapper.ruleSet ?? {}
        };
        return this.apiService.rules.saveRuleSetWrapperApiRulesSavePost(ruleSetWrapperCreate)

    }

    public getOrCreateRuleSetWrapper(category: CategoryRead,
                                     categoryType: TransactionTypeEnum): Observable<RuleSetWrapperRead> {
        const getOrCreateRuleSetWrapper: GetOrCreateRuleSetWrapperRequest = {
            categoryQualifiedName: category.qualifiedName,
            type: categoryType,
        };
        return this.apiService.rules.getOrCreateRuleSetWrapperApiRulesGetOrCreatePost(getOrCreateRuleSetWrapper)

    }

    public categorizeTransactions(userName: string): Observable<TransactionsCategorizationResponse> {
        return this.apiService.rules.categorizeTransactionsApiRulesCategorizeTransactionsPost()
            .pipe(map((r: CategorizeTransactionsResponse) => {
                    return {
                        message: r.message,
                        withCategoryCount: r.withCategoryCount,
                        withoutCategoryCount: r.withoutCategoryCount

                    }
                }
            ))


    }

    public saveBankAccountAlias(bankAccount: BankAccountRead): Observable<any> {

        const saveAlias: SaveAliasRequest = {
            alias: bankAccount.alias as string,
            bankAccount: bankAccount.accountNumber
        }
        return this.apiService.bankAccounts.saveAliasApiBankAccountsSaveAliasPost(saveAlias)

    }

    public getCategoryDetailsForPeriod(revenueExpensesQuery: RevenueExpensesQueryWithCategory): Observable<CategoryDetailsForPeriodResponse> {
        return this.apiService.analysis.getCategoryDetailsForPeriodApiAnalysisCategoryDetailsForPeriodPost(
            revenueExpensesQuery);

    }

    public getCategoriesForAccountAndTransactionType(accountNumber: string,
                                                     transactionType: TransactionTypeEnum): Observable<Array<string>> {

        return this.apiService.analysis.getCategoriesForAccountAndTransactionTypeApiAnalysisCategoriesForAccountGet(
            accountNumber, transactionType)
            .pipe(map((response: CategoriesForAccountResponse) => response.categories ?? []))

    }
}
