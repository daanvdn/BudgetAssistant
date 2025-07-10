import {HttpClient, HttpEvent, HttpResponse} from '@angular/common/http';
import {Injectable} from '@angular/core';
import {BehaviorSubject, map, Observable, of, shareReplay, Subject, tap} from 'rxjs';
import { firstValueFrom } from 'rxjs';

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

    public sharedCategoryTreeObservable$: Observable<SimplifiedCategory[]> = of([]);
    public sharedCategoryTreeExpensesObservable$: Observable<SimplifiedCategory[]>;
    public sharedCategoryTreeRevenueObservable$: Observable<SimplifiedCategory[]>;
    public fileUploadComplete$ = new Subject<void>();
    public selectedBankAccount$ = new BehaviorSubject<BankAccount | undefined>(undefined);
    public selectedBankAccountObservable$ = this.selectedBankAccount$.asObservable();
    public categoryMapSubject = new BehaviorSubject<CategoryMap | undefined >(undefined);
    public categoryMapObservable$ = this.categoryMapSubject.asObservable();
    refreshBankAccounts = new BehaviorSubject<boolean | undefined>( undefined);
    refreshBankAccountsObservable$ = this.refreshBankAccounts.asObservable();


    private backendUrl = environment.API_BASE_PATH;

    constructor(private http: HttpClient, private authService: AuthService,
                private apiBudgetAssistantBackendClientService: ApiBudgetAssistantBackendClientService) {


        this.sharedCategoryTreeExpensesObservable$ = this.getSharedCategoryTreeExpensesObservable$();
        this.sharedCategoryTreeRevenueObservable$ = this.getSharedCategoryTreeRevenueObservable$();
        (async () => {
            let categories: SimplifiedCategory[] = await this.getMergedCategoryTreeData();
            this.categoryMapSubject.next(new CategoryMap(categories));
            this.sharedCategoryTreeObservable$ = of(categories);
        })();


    }

    public triggerRefreshBankAccounts() {
        this.refreshBankAccounts.next(true);
    }


    private getSharedCategoryTreeRevenueObservable$() {
        return this.apiBudgetAssistantBackendClientService.apiCategoryTreeRetrieve('REVENUE').pipe(
            map(categoryTree => {
                let childrenCast: Array<SimplifiedCategory>  = []
                let children = categoryTree.root.children;
                for (let childObj of children) {
                    childrenCast.push(childObj as unknown as SimplifiedCategory);
                }
                return childrenCast;
            }),
            // Cache the result and share it with all subscribers
            shareReplay(1)
        );
    }

    private getSharedCategoryTreeExpensesObservable$(): Observable<SimplifiedCategory[]> {
        return this.apiBudgetAssistantBackendClientService.apiCategoryTreeRetrieve('EXPENSES').pipe(
            map(categoryTree => {
                let childrenCast: Array<SimplifiedCategory>  = []
                let children = categoryTree.root.children;
                for (let childObj of children) {
                    childrenCast.push(childObj as unknown as SimplifiedCategory);
                }
                return childrenCast;
            }),
            // Cache the result and share it with all subscribers
            shareReplay(1)
        );
    }

    // The convertSimplifiedCategoryToCategoryNode method has been removed as we now use SimplifiedCategory directly


    private async getMergedCategoryTreeData(): Promise<SimplifiedCategory[]> {

        let allData: SimplifiedCategory[] = [];
        let expenses = await firstValueFrom(this.sharedCategoryTreeExpensesObservable$);
        let revenue = await firstValueFrom(this.sharedCategoryTreeRevenueObservable$);

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


        return this.apiBudgetAssistantBackendClientService.apiBankAccountsList('body');


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
        //const number =    transactionsPage.number-1
        let page =  {
            content: transactionsPage.content,
            number: transactionsPage.number-1,
            size: transactionsPage.size,
            totalElements: transactionsPage.totalElements
        };
         return page;
    }

    public pageTransactions(request: PageRequest<Transaction>,
                            transactionQuery: TransactionQuery | undefined): Observable<Page<Transaction>> {
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
            page: request.page+1,
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
            page: request.page++,
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
