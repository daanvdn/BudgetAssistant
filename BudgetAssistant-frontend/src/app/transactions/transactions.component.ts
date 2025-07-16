import {AsyncPipe, DatePipe, NgIf, TitleCasePipe} from '@angular/common';
import {
    AfterViewInit,
    ChangeDetectionStrategy,
    ChangeDetectorRef,
    Component,
    effect,
    Input,
    OnDestroy,
    OnInit,
    ViewChild
} from '@angular/core';
import {MatDialog} from '@angular/material/dialog';
import {MatPaginator} from '@angular/material/paginator';
import {MatRadioButton, MatRadioChange, MatRadioGroup} from '@angular/material/radio';
import {MatSort, MatSortHeader} from '@angular/material/sort';
import {
    MatCell,
    MatCellDef,
    MatColumnDef,
    MatHeaderCell,
    MatHeaderCellDef,
    MatHeaderRow,
    MatHeaderRowDef,
    MatRow,
    MatRowDef,
    MatTable
} from '@angular/material/table';
import {AppService} from '../app.service';
import {AmountType, CategoryMap, CompositeTransactionsFileUploadResponse, FileWrapper, inferAmountType} from '../model';
import {TanstackPaginatedDataSource} from '../tanstack-paginated-datasource';
// Keep PaginationDataSource for backward compatibility during migration
import {PaginationDataSource} from 'ngx-pagination-data-source';
import {BankAccountSelectionComponent} from '../bank-account-selection/bank-account-selection.component';
import {TransactionSearchDialogComponent} from '../transaction-search-dialog/transaction-search-dialog.component';
import {AuthService} from "../auth/auth.service";
import {HttpEventType, HttpResponse} from "@angular/common/http";
import {ErrorDialogService} from "../error-dialog/error-dialog.service";
import {faTag} from "@fortawesome/free-solid-svg-icons";
import {Router} from "@angular/router";
import {Transaction, TransactionQuery, TransactionTypeEnum} from '@daanvdn/budget-assistant-client';
import {MatToolbar} from '@angular/material/toolbar';
import {MatProgressSpinner} from '@angular/material/progress-spinner';
import {MatButton} from '@angular/material/button';
import {MatIcon} from '@angular/material/icon';
import {MatTooltip} from '@angular/material/tooltip';
import {MatBadge} from '@angular/material/badge';
import {FaIconComponent} from '@fortawesome/angular-fontawesome';
import {CategoryTreeDropdownComponent} from '../category-tree-dropdown/category-tree-dropdown.component';
import {DateUtilsService} from '../shared/date-utils.service';
import {Subject, takeUntil, firstValueFrom} from "rxjs";


enum ViewType {
    INITIAL_VIEW = "INITIAL_VIEW",
    RUN_QUERY = "RUN_QUERY",
    SHOW_ALL = "SHOW_ALL",
    UPLOAD_TRANSACTIONS = "UPLOAD_TRANSACTIONS",
}


@Component({
    selector: 'app-transactions',
    templateUrl: './transactions.component.html',
    styleUrls: ['./transactions.component.scss'],
    standalone: true,
    changeDetection: ChangeDetectionStrategy.OnPush,
    imports: [MatToolbar, NgIf, MatProgressSpinner, BankAccountSelectionComponent, MatButton, MatIcon, MatTooltip, MatBadge, FaIconComponent, MatPaginator, MatTable, MatSort, MatColumnDef, MatHeaderCellDef, MatHeaderCell, MatSortHeader, MatCellDef, MatCell, CategoryTreeDropdownComponent, MatRadioGroup, MatRadioButton, MatHeaderRowDef, MatHeaderRow, MatRowDef, MatRow, AsyncPipe, TitleCasePipe, DatePipe]
})
export class TransactionsComponent implements OnInit, AfterViewInit, OnDestroy {
    private destroy$ = new Subject<void>();
    protected readonly ViewType = ViewType;
    protected readonly faTag = faTag;


    //table stuff
    @ViewChild(MatPaginator, {static: false}) paginator!: MatPaginator;
    @ViewChild(MatSort, {static: false}) sort!: MatSort;
    @ViewChild(MatTable) table!: MatTable<Transaction>;
    @ViewChild(BankAccountSelectionComponent) accountSelectionComponent!: BankAccountSelectionComponent;
    private currentSort?: any;


    filesAreUploading = false; // Add this line
    transactionToManuallyReview!: number;

    dataSource: TanstackPaginatedDataSource<Transaction, TransactionQuery>;
    // Define columns as readonly to prevent unnecessary recreation
    readonly displayedColumns = [
        "bookingDate",
        "counterparty",
        "transaction",
        "amount",
        "transactionType"
    ];

    // Add trackBy function to improve rendering performance
    trackByFn(index: number, item: Transaction): string {
        return item.transactionId || index.toString();
    }

    transactionQuery?: TransactionQuery;
    transactionQueryAsJson?: string;
    selectedAccount?: string;

    @ViewChild('fileInput') fileInput: any;

    viewType: ViewType = ViewType.INITIAL_VIEW;
    categoryMap?: CategoryMap;


    constructor(private appService: AppService, private authService: AuthService, public dialog: MatDialog,
                public datepipe: DatePipe, private errorDialogService: ErrorDialogService, private router: Router,
                private dateUtils: DateUtilsService, private cdr: ChangeDetectorRef) {
        this.dataSource = this.initDataSource(undefined); // Initialize dataSource with undefined account

        // Only initialize dataSource if it's not provided via @Input()
        /*
         if (!this.dataSource) {
         let account = undefined;
         this.dataSource = this.initDataSource(account);
         }
         */
        effect(() => {

            const categoryMap = this.appService.categoryMap();
            if (categoryMap) {
                this.categoryMap = categoryMap;
                this.cdr.markForCheck();
            }
        });

        effect(() => {
            const selectedBankAccount = this.appService.selectedBankAccount();
            if (selectedBankAccount && selectedBankAccount.accountNumber) {
                this.appService.countTransactionToManuallyReview(selectedBankAccount.accountNumber)
                    .pipe(takeUntil(this.destroy$))
                    .subscribe(count => {
                        this.transactionToManuallyReview = count.valueOf();
                        // Only mark for check instead of triggering a full change detection cycle
                        this.cdr.markForCheck();
                    });
            }
            else {
                // Set a default value if bankAccount or accountNumber is undefined
                this.transactionToManuallyReview = 0;
                // Only mark for check instead of triggering a full change detection cycle
                this.cdr.markForCheck();
            }

        })


    }

    showTransactionsToManuallyReview() {
        // Check if there are transactions to manually review before navigating
        if (this.transactionToManuallyReview !== undefined &&
            this.transactionToManuallyReview !== null &&
            this.transactionToManuallyReview > 0) {
            this.router.navigate(['/categorieën']);
        }
        else {
            console.error('No transactions to manually review or count is undefined');
        }
    }

    onClickFileInputButton(): void {
        this.fileInput.nativeElement.click();
    }

    onChangeFileInput(): void {
        this.filesAreUploading = true;
        let files: File[] = this.fileInput.nativeElement.files;
        let fileWrapperArray: FileWrapper[] = [];

        for (let index = 0; index < files.length; index++) {
            const file = files[index];
            fileWrapperArray.push({file: file, inProgress: false, progress: 0, failed: false});
        }

        let currentUser = this.authService.getUser();
        if (!currentUser || !currentUser.userName) {
            this.errorDialogService.openErrorDialog("Cannot upload transactions!", "User is not defined");
            return;
        }
        this.appService.uploadTransactionFiles(fileWrapperArray, currentUser.userName).subscribe(result => {

            if (result.type === HttpEventType.Response) {


                let response = result as HttpResponse<CompositeTransactionsFileUploadResponse>
                let uploadTimestamp = response.body?.uploadTimestamp;
                if (uploadTimestamp === undefined) {
                    this.filesAreUploading = false;
                    throw new Error("uploadTimestamp is undefined");
                }

                this.appService.triggerRefreshBankAccounts();
                let newSort;
                if (this.currentSort !== undefined) {
                    newSort = this.currentSort;
                }
                else {

                    newSort = {property: 'bookingDate', order: 'desc'}
                    this.currentSort = newSort;
                }

                let transactionQuery: TransactionQuery = {
                    transactionType: TransactionTypeEnum.BOTH,
                    counterpartyName: undefined,
                    minAmount: undefined,
                    maxAmount: undefined,
                    accountNumber: undefined,
                    categoryId: undefined,
                    counterpartyAccountNumber: undefined,
                    startDate: undefined,
                    endDate: undefined,
                    transactionOrCommunication: undefined,
                    uploadTimestamp: uploadTimestamp
                }

                // Set the initial query and sort
                this.dataSource.setQuery(transactionQuery);
                this.dataSource.setSort(newSort);
                this.viewType = ViewType.UPLOAD_TRANSACTIONS;
                this.filesAreUploading = false;
                // Mark for check to update the view
                this.cdr.markForCheck();

                if (this.selectedAccount) {
                    this.appService.countTransactionToManuallyReview(this.selectedAccount)
                        .pipe(takeUntil(this.destroy$))
                        .subscribe(count => {
                            this.transactionToManuallyReview = count.valueOf();
                            // Mark for check to update the view
                            this.cdr.markForCheck();
                        });
                }


            }


        })


    }


    amountType(transaction: Transaction): AmountType {
        if (transaction.amount === undefined || transaction.amount === null) {
            return AmountType.BOTH;
        }
        return inferAmountType(transaction.amount)


    }

    parseDate(dateStr: string | undefined | null): Date | null {
        return this.dateUtils.parseDate(dateStr);
    }

    openDialog(): void {


        const dialogRef = this.dialog.open(TransactionSearchDialogComponent, {
            restoreFocus: false
        });

        dialogRef.afterClosed().subscribe(result => {
            // console.log('The dialog was closed');
            if (result === undefined) {
                return;
            }
            else {
                this.transactionQuery = result;
                if (this.transactionQuery != undefined) {
                    this.transactionQuery.accountNumber = this.selectedAccount;

                }

            }
            if (this.transactionQuery !== undefined) {
                this.transactionQueryAsJson = JSON.stringify(this.transactionQuery)
            }
            this.doQuery(this.transactionQuery)
        });

    }

    handleAccountChange() {
        // Check if selectedBankAccount exists before accessing its properties
        if (!this.accountSelectionComponent || !this.accountSelectionComponent.selectedBankAccount) {
            console.error('Selected bank account is undefined in handleAccountChange');
            return;
        }

        this.selectedAccount = this.accountSelectionComponent.selectedBankAccount.accountNumber;
        if (this.selectedAccount === undefined || this.selectedAccount === this.appService.DUMMY_BANK_ACCOUNT) {
            console.error('Selected account number is undefined or dummy in handleAccountChange');
            return;
        }

        this.transactionQuery = {
            transactionType: TransactionTypeEnum.BOTH,
            counterpartyName: undefined,
            minAmount: undefined,
            maxAmount: undefined,
            accountNumber: this.selectedAccount,
            categoryId: undefined,
            counterpartyAccountNumber: undefined,
            startDate: undefined,
            endDate: undefined,
            transactionOrCommunication: undefined,
            uploadTimestamp: undefined
        }

        this.doQuery(this.transactionQuery);
        // No need to call markForCheck here as doQuery already does it
    }

    showAllTransactions() {
        let query = {} as TransactionQuery;
        query.accountNumber = this.selectedAccount;
        this.transactionQuery = query;
        this.viewType = ViewType.SHOW_ALL;
        this.dataSource.setQuery(query);
        // Mark for check to update the view
        this.cdr.markForCheck();
    }

    ngAfterViewInit(): void {
        // If dataSource exists, attach paginator and sort
        if (this.dataSource && this.paginator && this.sort) {
            this.dataSource.attachPaginator(this.paginator);
            this.dataSource.attachSort(this.sort);
        }
    }


    ngOnInit() {

    }

    ngOnDestroy() {
        this.destroy$.next();
        this.destroy$.complete();
    }


    private initDataSource(account: string | undefined): TanstackPaginatedDataSource<Transaction, TransactionQuery> {
        let query = {} as TransactionQuery;
        if (account !== undefined) {
            query.accountNumber = account;
        }

        // Create a new TanstackPaginatedDataSource using the pageTransactionsQuery
        return new TanstackPaginatedDataSource<Transaction, TransactionQuery>(
            (params) => this.appService.pageTransactions(params));
    }


    saveTransaction(transaction: Transaction) {
        this.appService.saveTransaction(transaction)
    }

    setIsRecurring(transaction: Transaction, event: MatRadioChange) {
        transaction.isRecurring = event.value;
        this.saveTransaction(transaction);
        // Mark for check to update the view
        this.cdr.markForCheck();
    }


    setIsAdvanceSharedAccount(transaction: Transaction, event: MatRadioChange) {
        transaction.isAdvanceSharedAccount = event.value;
        this.saveTransaction(transaction);
        // Mark for check to update the view
        this.cdr.markForCheck();
    }


    setCategory(transaction: Transaction, selectedCategoryQualifiedNameStr: string) {
        let category = this.categoryMap?.getSimpleCategory(selectedCategoryQualifiedNameStr);
        if (!category) {
            throw new Error("No category found for " + selectedCategoryQualifiedNameStr);
        }
        transaction.category = category;
        this.saveTransaction(transaction);
        // Mark for check to update the view
        this.cdr.markForCheck();
    }

    sortBy(event: any) {
        if (this.dataSource) {
            let key = event.active;
            let direction = event.direction;
            this.currentSort = {
                property: key,
                order: direction || "asc"
            };
            // Use setSort method for TanstackPaginatedDataSource
            this.dataSource.setSort(this.currentSort);
            // Mark for check to update the view
            this.cdr.markForCheck();
        }
    }

    doQuery(transactionQuery: TransactionQuery | undefined): void {
        if (transactionQuery === undefined) {
            return;
        }

        let newSort;
        if (this.currentSort !== undefined) {
            newSort = this.currentSort;
        }
        else {

            newSort = {property: 'bookingDate', order: 'desc'}
            this.currentSort = newSort;
        }

        this.dataSource.setQuery(transactionQuery);
        this.dataSource.setSort(newSort);

        this.viewType = ViewType.RUN_QUERY;
        // Mark for check to update the view
        this.cdr.markForCheck();
    }


    getNrOfTransactionsToManuallyReview(): string {
        if (this.transactionToManuallyReview !== undefined && this.transactionToManuallyReview !== null) {
            return this.transactionToManuallyReview.toString();
        }
        return "";
    }

    getNrOfTransactionsToManuallyReviewTooltip(): string {
        if (this.transactionToManuallyReview !== undefined && this.transactionToManuallyReview !== null) {
            return `You have ${this.transactionToManuallyReview} transactions to manually review`;
        }
        return "";
    }
}
