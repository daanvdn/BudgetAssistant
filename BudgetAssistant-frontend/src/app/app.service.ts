import {HttpClient, HttpEvent} from '@angular/common/http';
import {Injectable} from '@angular/core';
import {BehaviorSubject, map, Observable, of, Subject, tap} from 'rxjs';
import {
    FileWrapper,
    ResolvedStartEndDateShortcut,
    resolveTransactionCategory,
    StartEndDateShortcut,
    TransactionWithCategory
} from './model';
import {AuthService} from "./auth/auth.service";
import {
    BankAccountRead,
    BudgetAssistantApiService,
    CategoriesForAccountResponse,
    CategoryDetailsForPeriodResponse,
    CategoryIndex,
    CategoryRead,
    DateRangeShortcut,
    Grouping,
    ResolvedDateRange,
    RevenueExpensesQuery,
    RevenueExpensesQueryWithCategory,
    SaveAliasRequest,
    TransactionRead,
    TransactionTypeEnum,
    UploadTransactionsResponse
} from "@daanvdn/budget-assistant-client";
import {environment} from "../environments/environment";


@Injectable({
    providedIn: 'root'
})
export class AppService {

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

    public sharedCategoryTree: BehaviorSubject<CategoryRead[]> = new BehaviorSubject<CategoryRead[]>([]);
    public sharedCategoryTreeExpenses: BehaviorSubject<CategoryRead[]> = new BehaviorSubject<CategoryRead[]>([]);
    public sharedCategoryTreeRevenue: BehaviorSubject<CategoryRead[]> = new BehaviorSubject<CategoryRead[]>([]);
    public fileUploadComplete$ = new Subject<void>();
    public selectedBankAccount$ = new BehaviorSubject<BankAccountRead | undefined>(undefined);
    public selectedBankAccountObservable$ = this.selectedBankAccount$.asObservable();
    public categoryIndexSubject = new BehaviorSubject<CategoryIndex | undefined>(undefined);
    public categoryIndexObservable$ = this.categoryIndexSubject.asObservable();
    refreshBankAccounts = new BehaviorSubject<boolean | undefined>(undefined);
    refreshBankAccountsObservable$ = this.refreshBankAccounts.asObservable();


    private backendUrl = environment.API_BASE_PATH;

    private idToCategoryIndex$ = new BehaviorSubject<{ [id: number]: CategoryRead }>({});

    constructor(private http: HttpClient, private authService: AuthService,
                private apiService: BudgetAssistantApiService) {

        // Fetch the category index once and derive all observables from it
        this.fetchAndStoreCategoryIndex();


    }

    public triggerRefreshBankAccounts() {
        this.refreshBankAccounts.next(true);
    }


    setBankAccount(bankAccount: BankAccountRead) {
        this.selectedBankAccount$.next(bankAccount);
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

    public countUncategorizedTransactions(bankAccountNumber: string): Observable<Number> {
        if (!bankAccountNumber) {
            console.error('Bank account number is undefined');
            return of(0); // Return observable with 0 if bankAccount or accountNumber is undefined
        }
        return this.apiService.transactions.countUncategorizedTransactionsApiTransactionsCountUncategorizedGet(
            bankAccountNumber).pipe(map(count => count.count));


    }

   /**
     * Parses an ISO 8601 date string (YYYY-MM-DD) into a Date object.
     * @param json The date string in ISO 8601 format (e.g., "2024-01-15")
     * @returns A Date object representing the parsed date
     */
    private parseDate(json: string): Date {
        let parts: string[] = json.split('-');
        let year: number = parseInt(parts[0]);
        let month: number = parseInt(parts[1]) - 1; // JavaScript months are 0-indexed
        let day: number = parseInt(parts[2]);
        return new Date(year, month, day);
    }

    public mapTransactionsWithCategory(transactions: TransactionRead[]): TransactionWithCategory[] {
        const index = this.idToCategoryIndex$.getValue();
        return transactions.map(t => resolveTransactionCategory(t, index));
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

    private fetchAndStoreCategoryIndex() {
        this.apiService.categories.getCategoryIndexApiCategoriesCategoryIndexGet().subscribe(index => {
            // Store the full CategoryIndex for lookups
            this.categoryIndexSubject.next(index);

            // Store the id-to-category mapping for transaction category resolution
            this.idToCategoryIndex$.next(index.idToCategoryIndex);

            // Push tree data to existing subscribers via BehaviorSubject.next()
            this.sharedCategoryTreeExpenses.next(index.expensesRootChildren ?? []);
            this.sharedCategoryTreeRevenue.next(index.revenueRootChildren ?? []);
            this.sharedCategoryTree.next([
                ...(index.expensesRootChildren ?? []),
                ...(index.revenueRootChildren ?? [])
            ]);
        });
    }

    /**
     * Get the category ID by its qualified name.
     * Returns the ID or undefined if not found.
     */
    public getCategoryIdByQualifiedName(qualifiedName: string): number | undefined {
        const index = this.categoryIndexSubject.getValue();
        if (!index || !qualifiedName) {
            return undefined;
        }
        return index.qualifiedNameToIdIndex[qualifiedName];
    }
}
