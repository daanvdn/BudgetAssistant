import {HttpClient, HttpEvent, HttpResponse} from '@angular/common/http';
import {effect, Injectable, signal} from '@angular/core';
import {BehaviorSubject, firstValueFrom, map, Observable, of, Subject, tap} from 'rxjs';
import {injectQuery} from '@tanstack/angular-query-experimental';
import {Page as TanstackPage, Sort} from './tanstack-paginated-datasource'
import {Page, PageRequest} from "ngx-pagination-data-source";
import {
    CategoryMap,
    DistributionByCategoryForPeriodHandlerResult2,
    FileWrapper, GroupBy,
    ResolvedStartEndDateShortcut,
    StartEndDateShortcut,
    TransactionsCategorizationResponse, TransactionTypeAndBankAccount
} from './model';
import {AuthService} from "./auth/auth.service";
import {BudgetTreeNode} from "./budget/budget.component";
import {
    ApiBudgetAssistantBackendClientService,
    BankAccount,
    BankAccountNumber,
    BudgetTreeNode as BudgetTreeNodeApi,
    CategoryDetailsForPeriodHandlerResult,
    ExpensesAndRevenueForPeriod,
    GetOrCreateRuleSetWrapper,
    GroupingEnum,
    PageTransactionsInContextRequest,
    PageTransactionsRequest,
    PageTransactionsToManuallyReviewRequest,
    ResolvedStartEndDateShortcut as ResolvedStartEndDateShortcutApi,
    RevenueAndExpensesPerPeriodResponse,
    RevenueExpensesQuery,
    RuleSetWrapper,
    SaveAlias,
    SimplifiedCategory,
    SortOrderEnum,
    SortPropertyEnum,
    SuccessfulOperationResponse,
    Transaction,
    TransactionInContextQuery,
    TransactionQuery,
    TransactionsPage,
    TransactionTypeEnum,
    TypeEnum
} from "@daanvdn/budget-assistant-client";
import {environment} from "../environments/environment";
import {UploadTransactionsResponse} from "@daanvdn/budget-assistant-client/dist/model/upload-transactions-response";
import {BudgetTree} from "@daanvdn/budget-assistant-client/dist/model/budget-tree";
import {
    RevenueExpensesQueryWithCategory
} from "@daanvdn/budget-assistant-client/dist/model/revenue-expenses-query-with-category";


@Injectable({
    providedIn: 'root'
})
export class AppService {

    public DUMMY_BANK_ACCOUNT = "dummy";
    private startDate$ = new BehaviorSubject<Date | undefined>(undefined);
    private endDate$ = new BehaviorSubject<Date |undefined>(undefined);
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

    public fileUploadComplete$ = new Subject<void>();
    public categoryMap = signal<CategoryMap | undefined>(undefined);
    public selectedBankAccount = signal<BankAccount | undefined>(undefined );


    public bankAccountsQuery = injectQuery(() => ({
        queryKey: ['bankAccounts'],
        queryFn: () => firstValueFrom(this.apiBudgetAssistantBackendClientService.apiBankAccountsList('body')),
        staleTime: 5 * 60 * 1000, // 5 minutes,
    }));


    public categoryTreeRevenueQuery = this.createCategoryTreeQuery('REVENUE');

    public categoryTreeExpensesQuery = this.createCategoryTreeQuery('EXPENSES');

    public categoryTreeBothQuery = injectQuery(() => ({
        queryKey: ['categoryTree', 'BOTH'],
        queryFn: async () => {
            // Get both revenue and expenses data
            try {
                const [revenueData, expensesData] = await Promise.all([
                    this.categoryTreeRevenueQuery.promise(),
                    this.categoryTreeExpensesQuery.promise()
                ]);


            // Merge the data (same logic as getMergedCategoryTreeData)
            let allData: SimplifiedCategory[] = [];
            allData = allData.concat(expensesData);

            for (const category of revenueData) {
                if (!(category.name === "NO CATEGORY" || category.name === "DUMMY CATEGORY")) {
                    allData.push(category);
                }
            }

            return allData;
            } catch (e) {
                console.error(`Error fetching category tree data: ${e}`);
                throw new Error(`Error fetching category tree data: ${e}`);
            }
        },
        staleTime: Infinity,
        enabled: true,
        experimental_prefetchInRender: true, // Enable prefetching in render

    }));



    private backendUrl = environment.API_BASE_PATH;

    constructor(private http: HttpClient, private authService: AuthService,
                private apiBudgetAssistantBackendClientService: ApiBudgetAssistantBackendClientService) {
        effect(() => {
            const categoriesData = this.categoryTreeBothQuery.data();
            const isSuccess = this.categoryTreeBothQuery.isSuccess();

            if (isSuccess && categoriesData) {
                this.categoryMap.set(new CategoryMap(categoriesData));

            }

        }, {allowSignalWrites: true})


    }

    public pageTransactions(params: {
        page: number;
        size: number;
        sort: Sort;
        query: TransactionQuery
    }): Observable<TanstackPage<Transaction>> {
        try {
            let pageTransactionsRequest: PageTransactionsRequest = {
                page: params.page + 1,
                size: params.size,
                sortOrder: params.sort.direction as SortOrderEnum,
                sortProperty: this.camelToSnake(params.sort.property) as SortPropertyEnum,
                query: params.query

            }
            return this.apiBudgetAssistantBackendClientService.apiTransactionsPageTransactionsCreate(
                pageTransactionsRequest).pipe(map((result: TransactionsPage) => {

                return this.toPage2(result);


            }));
        } catch (e: any) {
            throw new Error(`Error in pageTransactions2: ${e.message}`);
        }

    }



    private createCategoryTreeQuery(type: 'REVENUE' | 'EXPENSES') {
        return injectQuery(() => ({
            queryKey: ['categoryTree', type],
            queryFn: async () => {
                const categoryTree = await firstValueFrom(
                    this.apiBudgetAssistantBackendClientService.apiCategoryTreeRetrieve(type)
                );

                const childrenCast: Array<SimplifiedCategory> = [];
                const children = categoryTree.root.children;
                for (let childObj of children) {
                    childrenCast.push(childObj as unknown as SimplifiedCategory);
                }
                return childrenCast;
            },
            staleTime: Infinity,
            experimental_prefetchInRender: true, // Enable prefetching in render
        }));
    }


    public triggerRefreshBankAccounts() {
        this.bankAccountsQuery.refetch();
    }


    setBankAccount(bankAccount: BankAccount) {
        this.selectedBankAccount.set(bankAccount);
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


    public countTransactionToManuallyReview(bankAccountNumber: string): Observable<Number> {
        if (!bankAccountNumber) {
            console.error('Bank account number is undefined');
            return of(0); // Return observable with 0 if bankAccount or accountNumber is undefined
        }
        return this.apiBudgetAssistantBackendClientService.apiTransactionsCountTransactionsToManuallyReviewRetrieve(
            bankAccountNumber).pipe(map(count => count.count));


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
        let year: number = parseInt(parts[0])
        let month: number = parseInt(parts[1])
        let day: number = parseInt(parts[2])
        let dateObj = new Date();
        dateObj.setDate(day);
        dateObj.setMonth(month-1);
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
        //const number =    transactionsPage.number-1
        let page =  {
            content: transactionsPage.content,
            number: transactionsPage.number-1,
            size: transactionsPage.size,
            totalElements: transactionsPage.totalElements
        };
         return page;
    }
    private toPage2(transactionsPage: TransactionsPage): TanstackPage<Transaction> {
        //const number =    transactionsPage.number-1
        let page =  {
            content: transactionsPage.content,
            number: transactionsPage.number-1,
            size: transactionsPage.size,
            totalElements: transactionsPage.totalElements
        };
         return page;
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
            page: request.page++,
            size: request.size,
            sortOrder: tmpSortOrder as SortOrderEnum,
            sortProperty: this.camelToSnake(tmpSortProperty) as SortPropertyEnum,
            query: query

        }
        return this.apiBudgetAssistantBackendClientService.apiTransactionsPageTransactionsInContextCreate(
            pageTransactionsInContextRequest).pipe( map(result => {
            return this.toPage(result);
        }));
    }


    public pageTransactionsToManuallyReview(
        params: {
            page: number;
            size: number;
            sort: Sort;
            query: TransactionTypeAndBankAccount
        }): Observable<TanstackPage<Transaction | GroupBy>> {
        let tmpSortOrder = "asc";
        if (params.sort && params.sort.direction) {
            tmpSortOrder = params.sort.direction;
        }

        let tmpSortProperty = "counterparty";
        if (params.sort && params.sort.property) {

            tmpSortProperty = params.sort.property;
        }




        let pageTransactionsToManuallyReviewRequest : PageTransactionsToManuallyReviewRequest = {
            page: params.page + 1,
            size: params.size,
            sortOrder: tmpSortOrder as SortOrderEnum,
            sortProperty: this.camelToSnake(tmpSortProperty) as SortPropertyEnum,
            bankAccount: params.query.bankAccount.accountNumber,
            transactionType: params.query.transactionType,


        }

        function toGroupBy(transactionPage: TransactionsPage): TanstackPage<Transaction | GroupBy> {
            let mapByCounterpartyName = new Map<string, Transaction[]>();
            const transactions = transactionPage.content;

            for (const transaction of transactions) {
                let name = transaction.counterparty.name;
                if (!name) {
                    name = "";
                }
                let transactionsForCounterparty = mapByCounterpartyName.has(name) ? mapByCounterpartyName.get(
                    name) : [];
                transactionsForCounterparty?.push(transaction);
                mapByCounterpartyName.set(name, transactionsForCounterparty as Transaction[]);
            }
            let sortedKeys = Array.from(mapByCounterpartyName.keys()).sort();
            let result = new Array<Transaction | GroupBy>();
            for (const aKey of sortedKeys) {
                let transactionsForKey = mapByCounterpartyName.get(aKey) as Transaction[];
                let groupBy: GroupBy = {
                    counterparty: aKey, isGroupBy: true, transactions: transactionsForKey, isExpense:  params.query.transactionType === TransactionTypeEnum.EXPENSES
                };
                result.push(groupBy)
                result.push(...transactionsForKey)

            }
            let asPage: TanstackPage<Transaction | GroupBy> = {
                content: result,
                number: transactionPage.number - 1, // Adjusting to zero-based index
                size: transactionPage.size,
                totalElements: transactionPage.totalElements
            }

            return asPage;
        }

        return this.apiBudgetAssistantBackendClientService.apiTransactionsPageTransactionsToManuallyReviewCreate(pageTransactionsToManuallyReviewRequest).pipe(
            map(result => {
                return toGroupBy(result);
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
        return this.apiBudgetAssistantBackendClientService.apiResolveStartEndDateShortcutRetrieve(startEnDateShortCut,
            'body')
            .pipe(map((resolvedStartEndDateShortcutApi: ResolvedStartEndDateShortcutApi) => {
                //parse the ResolvedStartEndDateShortcutApi.start string and ResolvedStartEndDateShortcutApi.end string
                // to Date and return a new ResolvedStartEndDateShortcut object
                let start: Date = this.parseDate(resolvedStartEndDateShortcutApi.start);
                let end: Date = this.parseDate(resolvedStartEndDateShortcutApi.end);
                return new ResolvedStartEndDateShortcut(start, end);

            }));

    }


    public getDistinctCounterpartyNames(bankAccount: string): Observable<Array<string>> {

        return this.apiBudgetAssistantBackendClientService.apiDistinctCounterpartyNamesRetrieve(bankAccount, 'body')
    }

    public getDistinctCounterpartyAccounts(bankAccount: string): Observable<Array<string>> {
        return this.apiBudgetAssistantBackendClientService.apiDistinctCounterpartyAccountsRetrieve(bankAccount, 'body')
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
        return this.apiBudgetAssistantBackendClientService.apiTransactionsUploadTransactionsCreate(
            files,
            'events',
            true
        ).pipe(tap(() => {
            this.fileUploadComplete$.next();
        })) as Observable<HttpEvent<UploadTransactionsResponse>>;

    }

    public findOrCreateBudget(bankAccount: BankAccount): Observable<BudgetTreeNode[]> {

        const bankAccountNumber: BankAccountNumber = {
            bankAccountNumber: bankAccount.accountNumber
        }
        let obs: Observable<BudgetTree> = this.apiBudgetAssistantBackendClientService.apiFindOrCreateBudgetCreate(
            bankAccountNumber, 'body');
        return obs.pipe(map((budgetTree: BudgetTree) => {
            // Convert the BudgetTree to an array of BudgetTreeNode objects
            const result: BudgetTreeNode[] = [];

            // Process the root node and its children recursively
            this.convertBudgetTreeNodeApiToBudgetTreeNode(budgetTree.root, -1, result);

            return result;
        }));

    }

    private convertBudgetTreeNodeApiToBudgetTreeNode(apiNode: BudgetTreeNodeApi, parentId: number,
                                                     result: BudgetTreeNode[]): void {
        // Create a new BudgetTreeNode from the API node
        const localNode: BudgetTreeNode = {
            budgetTreeNodeAmount: apiNode.budgetTreeNodeAmount,
            budgetTreeNodeId: apiNode.budgetTreeNodeId,
            budgetTreeNodeParentId: parentId,
            children: [],
            name: apiNode.name,
            qualifiedName: apiNode.qualifiedName
        };

        // Add the node to the result array
        result.push(localNode);

        // Process children recursively
        if (apiNode.children && apiNode.children.length > 0) {
            for (const childObj of apiNode.children) {
                // Extract the child node from the object
                // Each childObj is expected to have only one key-value pair where the key is the name
                // and the value contains the node data
                const entries = Object.entries(childObj);
                if (entries.length > 1) {
                    console.warn(`childObj has ${entries.length} entries, but only the first one will be used.`, childObj);
                }
                const [childName, childValue] = entries[0];
                const childNode = childValue as unknown as BudgetTreeNodeApi;

                // Process the child node recursively
                this.convertBudgetTreeNodeApiToBudgetTreeNode(childNode, localNode.budgetTreeNodeId, result);

                // Add the converted child to the current node's children array
                localNode.children.push(result[result.length - 1]);
            }
        }
    }

    private convertBudgetTreeNodeToBudgetTreeNodeApi(node: BudgetTreeNode): BudgetTreeNodeApi {

        return {
            budgetTreeNodeAmount: node.budgetTreeNodeAmount,
            budgetTreeNodeId: node.budgetTreeNodeId,
            children: node.children.map(child => this.convertBudgetTreeNodeToBudgetTreeNodeApi(child)),
            name: node.name,
            qualifiedName: node.qualifiedName
        }
    }


    public updateBudgetEntryAmount(budgetEntry: BudgetTreeNode): Observable<HttpResponse<any>> {

        return this.apiBudgetAssistantBackendClientService.apiUpdateBudgetEntryAmountCreate(
            this.convertBudgetTreeNodeToBudgetTreeNodeApi(budgetEntry), 'response')

    }


    public saveRuleSetWrapper(ruleSetWrapper: RuleSetWrapper): Observable<SuccessfulOperationResponse> {
        return this.apiBudgetAssistantBackendClientService.apiSaveRuleSetWrapperCreate(ruleSetWrapper)

    }

    public getOrCreateRuleSetWrapper(category: SimplifiedCategory, categoryType: TypeEnum): Observable<RuleSetWrapper> {
        const getOrCreateRuleSetWrapper: GetOrCreateRuleSetWrapper = {
            categoryQualifiedName : category.qualifiedName,
            type:  categoryType,
        };
        return this.apiBudgetAssistantBackendClientService.apiGetOrCreateRuleSetWrapperCreate(getOrCreateRuleSetWrapper)

    }

    public categorizeTransactions(userName: string): Observable<TransactionsCategorizationResponse> {
        return this.apiBudgetAssistantBackendClientService.apiCategorizeTransactionsCreate("body").pipe(map(r => {
                return {
                    message: r.message,
                    withCategoryCount: r.withCategoryCount,
                    withoutCategoryCount: r.withoutCategoryCount

                }
        }
        ))


    }

    public saveBankAccountAlias(bankAccount: BankAccount): Observable<any> {

        const saveAlias: SaveAlias = {
            alias: bankAccount.alias as string,
            bankAccount: bankAccount.accountNumber
        }
        return this.apiBudgetAssistantBackendClientService.apiSaveAliasCreate(saveAlias, 'body')

    }

    public getCategoryDetailsForPeriod(revenueExpensesQuery: RevenueExpensesQueryWithCategory): Observable<CategoryDetailsForPeriodHandlerResult> {
        return this.apiBudgetAssistantBackendClientService.apiAnalysisCategoryDetailsForPeriodCreate(
            revenueExpensesQuery, 'body');

    }

    public getCategoriesForAccountAndTransactionType(accountNumber: string, transactionType: TransactionTypeEnum): Observable<Array<string>>{

        return this.apiBudgetAssistantBackendClientService.apiAnalysisCategoriesForAccountAndTransactionTypeRetrieve(
            accountNumber, transactionType, 'body')

    }
}
