import {CommonModule, DatePipe, TitleCasePipe} from '@angular/common';
import {Component, computed, DestroyRef, inject, OnInit, signal, ViewChild} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {MatDialog} from '@angular/material/dialog';
import {MatPaginator, PageEvent} from '@angular/material/paginator';
import {MatRadioButton, MatRadioChange, MatRadioGroup} from '@angular/material/radio';
import {MatSort, MatSortHeader, Sort} from '@angular/material/sort';
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
import {MatToolbar} from '@angular/material/toolbar';
import {MatProgressSpinner} from '@angular/material/progress-spinner';
import {MatIconButton} from '@angular/material/button';
import {MatIcon} from '@angular/material/icon';
import {MatTooltip} from '@angular/material/tooltip';
import {MatBadge} from '@angular/material/badge';
import {MatSnackBar, MatSnackBarModule} from '@angular/material/snack-bar';
import {MatCard, MatCardContent} from '@angular/material/card';
import {FaIconComponent} from '@fortawesome/angular-fontawesome';
import {faTag} from '@fortawesome/free-solid-svg-icons';
import {Router} from '@angular/router';
import {
  BudgetAssistantApiService,
  CategoryIndex,
  PageTransactionsRequest,
  SortOrder,
  TransactionQuery,
  TransactionSortProperty,
  TransactionTypeEnum,
  TransactionUpdate,
  UploadTransactionsResponse
} from '@daanvdn/budget-assistant-client';
import {injectMutation, injectQuery, injectQueryClient, QueryClient} from '@tanstack/angular-query-experimental';
import {firstValueFrom} from 'rxjs';

import {AppService} from '../app.service';
import {AmountType, inferAmountType, TransactionWithCategory} from '../model';
import {BankAccountSelectionComponent} from '../bank-account-selection/bank-account-selection.component';
import {TransactionSearchDialogComponent} from '../transaction-search-dialog/transaction-search-dialog.component';
import {AuthService} from '../auth/auth.service';
import {ErrorDialogService} from '../error-dialog/error-dialog.service';
import {CategoryTreeDropdownComponent} from '../category-tree-dropdown/category-tree-dropdown.component';
import {HttpEventType, HttpResponse} from '@angular/common/http';

enum ViewType {
  INITIAL_VIEW = 'INITIAL_VIEW',
  RUN_QUERY = 'RUN_QUERY',
  SHOW_ALL = 'SHOW_ALL',
  UPLOAD_TRANSACTIONS = 'UPLOAD_TRANSACTIONS',
}

interface SortConfig {
  property: TransactionSortProperty;
  order: SortOrder;
}

interface PaginationState {
  page: number;
  size: number;
  totalElements: number;
  totalPages: number;
}

@Component({
  selector: 'app-transactions',
  templateUrl: './transactions.component.html',
  styleUrls: ['./transactions.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    MatToolbar,
    MatProgressSpinner,
    BankAccountSelectionComponent,
    MatIconButton,
    MatIcon,
    MatTooltip,
    MatBadge,
    FaIconComponent,
    MatPaginator,
    MatTable,
    MatSort,
    MatColumnDef,
    MatHeaderCellDef,
    MatHeaderCell,
    MatSortHeader,
    MatCellDef,
    MatCell,
    CategoryTreeDropdownComponent,
    MatRadioGroup,
    MatRadioButton,
    MatHeaderRowDef,
    MatHeaderRow,
    MatRowDef,
    MatRow,
    TitleCasePipe,
    MatSnackBarModule,
    MatCard,
    MatCardContent
  ],
  providers: [DatePipe]
})
export class TransactionsComponent implements OnInit {
  // Dependency injection
  private readonly destroyRef = inject(DestroyRef);
  private readonly appService = inject(AppService);
  private readonly authService = inject(AuthService);
  private readonly apiService = inject(BudgetAssistantApiService);
  private readonly dialog = inject(MatDialog);
  private readonly datePipe = inject(DatePipe);
  private readonly errorDialogService = inject(ErrorDialogService);
  private readonly router = inject(Router);
  private readonly snackBar = inject(MatSnackBar);
  private readonly queryClient = inject(QueryClient);

  // Icon
  protected readonly faTag = faTag;

  // ViewChild references
  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;
  @ViewChild(MatTable) table!: MatTable<TransactionWithCategory>;
  @ViewChild(BankAccountSelectionComponent) accountSelectionComponent!: BankAccountSelectionComponent;
  @ViewChild('fileInput') fileInput: any;

  // Signals for state management
  protected readonly viewType = signal<ViewType>(ViewType.INITIAL_VIEW);
  protected readonly selectedAccount = signal<string | undefined>(undefined);
  protected readonly transactionQuery = signal<TransactionQuery | undefined>(undefined);
  protected readonly filesAreUploading = signal(false);
  protected readonly transactionsToManuallyReview = signal(0);
  protected readonly categoryIndex = signal<CategoryIndex | undefined>(undefined);

  // Computed signal to check if category index is ready for mapping
  protected readonly isCategoryIndexReady = computed(() => {
    const index = this.categoryIndex();
    return index !== undefined && Object.keys(index.idToCategoryIndex).length > 0;
  });

  // Pagination state
  protected readonly currentPage = signal(0);
  protected readonly pageSize = signal(20);
  protected readonly sortConfig = signal<SortConfig>({
    property: 'booking_date' as TransactionSortProperty,
    order: 'desc' as SortOrder
  });

  // Table configuration
  protected readonly displayedColumns = [
    'bookingDate',
    'counterparty',
    'transaction',
    'amount',
    'transactionType'
  ];

  // Computed values
  protected readonly viewTypeLabel = computed(() => {
    switch (this.viewType()) {
      case ViewType.RUN_QUERY:
        return 'Search results';
      case ViewType.SHOW_ALL:
        return 'All transactions';
      case ViewType.UPLOAD_TRANSACTIONS:
        return 'Uploaded transactions';
      default:
        return '';
    }
  });

  protected readonly hasViewTypeLabel = computed(() => {
    return this.viewType() !== ViewType.INITIAL_VIEW;
  });

  // TanStack Query for transactions
  transactionsQuery = injectQuery(() => ({
    queryKey: ['transactions', this.selectedAccount(), this.currentPage(), this.pageSize(), this.sortConfig(), this.transactionQuery()],
    queryFn: async () => {
      const account = this.selectedAccount();
      const query = this.transactionQuery();

      const request: PageTransactionsRequest = {
        page: this.currentPage(),
        size: this.pageSize(),
        sortOrder: this.sortConfig().order,
        sortProperty: this.sortConfig().property,
        query: query ? {...query, accountNumber: query.accountNumber || account} : {accountNumber: account}
      };

      const result = await firstValueFrom(
          this.apiService.transactions.pageTransactionsApiTransactionsPagePost(request)
      );

      return {
        ...result,
        content: this.appService.mapTransactionsWithCategory(result.content)
      };
    },
    enabled: !!this.selectedAccount() && this.isCategoryIndexReady(),
    staleTime: 30000, // 30 seconds
    refetchOnWindowFocus: false
  }));

  // Computed signals for template
  protected readonly transactions = computed(() => {
    return this.transactionsQuery.data()?.content ?? [];
  });

  protected readonly pagination = computed<PaginationState>(() => {
    const data = this.transactionsQuery.data();
    return {
      page: data?.page ?? 0,
      size: data?.size ?? this.pageSize(),
      totalElements: data?.totalElements ?? 0,
      totalPages: data?.totalPages ?? 0
    };
  });

  protected readonly isLoading = computed(() => {
    return this.transactionsQuery.isPending() || this.filesAreUploading();
  });

  protected readonly isEmpty = computed(() => {
    return !this.isLoading() && this.transactions().length === 0 && this.selectedAccount();
  });

  protected readonly isEmptyDueToSearch = computed(() => {
    return this.isEmpty() && this.viewType() === ViewType.RUN_QUERY;
  });

  // Save transaction mutation
  saveTransactionMutation = injectMutation(() => ({
    mutationFn: async (params: { transactionId: string; update: TransactionUpdate }) => {
      return firstValueFrom(
          this.apiService.transactions.saveTransactionApiTransactionsSavePost(
              params.transactionId,
              params.update
          )
      );
    },
    onSuccess: () => {
      this.snackBar.open('Transaction saved', 'Close', {duration: 2000});
    },
    onError: (error: any) => {
      console.error('Error saving transaction:', error);
      this.snackBar.open('Failed to save transaction', 'Close', {duration: 3000});
    }
  }));

  ngOnInit(): void {
    // Subscribe to category index updates
    this.appService.categoryIndexObservable$
        .pipe(takeUntilDestroyed(this.destroyRef))
        .subscribe(categoryIndex => {
          this.categoryIndex.set(categoryIndex);
        });

    // Subscribe to selected bank account changes
    this.appService.selectedBankAccountObservable$
        .pipe(takeUntilDestroyed(this.destroyRef))
        .subscribe(bankAccount => {
          if (bankAccount?.accountNumber) {
            this.loadTransactionsToManuallyReviewCount(bankAccount.accountNumber);
          }
          else {
            this.transactionsToManuallyReview.set(0);
          }
        });
  }

  private loadTransactionsToManuallyReviewCount(accountNumber: string): void {
    this.appService.countTransactionToManuallyReview(accountNumber)
        .pipe(takeUntilDestroyed(this.destroyRef))
        .subscribe({
          next: count => this.transactionsToManuallyReview.set(count.valueOf()),
          error: () => this.transactionsToManuallyReview.set(0)
        });
  }

  // Event handlers
  handleAccountChange(): void {
    if (!this.accountSelectionComponent?.selectedBankAccount) {
      console.error('Selected bank account is undefined');
      return;
    }

    const accountNumber = this.accountSelectionComponent.selectedBankAccount.accountNumber;
    if (!accountNumber || accountNumber === this.appService.DUMMY_BANK_ACCOUNT) {
      console.error('Invalid account number');
      return;
    }

    this.selectedAccount.set(accountNumber);
    this.transactionQuery.set({
      transactionType: TransactionTypeEnum.BOTH,
      accountNumber: accountNumber
    });
    this.currentPage.set(0);
    this.viewType.set(ViewType.SHOW_ALL);
  }

  showAllTransactions(): void {
    const account = this.selectedAccount();
    if (!account) {
      this.snackBar.open('Please select a bank account first', 'Close', {duration: 3000});
      return;
    }

    this.transactionQuery.set({
      transactionType: TransactionTypeEnum.BOTH,
      accountNumber: account
    });
    this.currentPage.set(0);
    this.viewType.set(ViewType.SHOW_ALL);
  }

  showTransactionsToManuallyReview(): void {
    if (this.transactionsToManuallyReview() > 0) {
      this.router.navigate(['/categorieën']);
    }
    else {
      this.snackBar.open('No transactions to manually review', 'Close', {duration: 3000});
    }
  }

  onClickFileInputButton(): void {
    this.fileInput.nativeElement.click();
  }

  async onChangeFileInput(): Promise<void> {
    const files: FileList = this.fileInput.nativeElement.files;
    if (!files || files.length === 0) {
      return;
    }

    const currentUser = this.authService.getUser();
    if (!currentUser?.userName) {
      this.errorDialogService.openErrorDialog('Cannot upload transactions!', 'User is not defined');
      return;
    }

    this.filesAreUploading.set(true);

    const fileWrappers = Array.from(files).map(file => ({
      file,
      inProgress: false,
      progress: 0,
      failed: false
    }));

    this.appService.uploadTransactionFiles(fileWrappers, currentUser.userName)
        .pipe(takeUntilDestroyed(this.destroyRef))
        .subscribe({
          next: (event) => {
            if (event.type === HttpEventType.Response) {
              const response = event as HttpResponse<UploadTransactionsResponse>;
              const uploadTimestamp = response.body?.uploadTimestamp;

              if (!uploadTimestamp) {
                this.filesAreUploading.set(false);
                this.errorDialogService.openErrorDialog('Upload Error', 'Upload timestamp is undefined');
                return;
              }

              // Refresh bank accounts
              this.appService.triggerRefreshBankAccounts();

              // Update query to show uploaded transactions
              this.transactionQuery.set({
                transactionType: TransactionTypeEnum.BOTH,
                uploadTimestamp: uploadTimestamp,
                accountNumber: this.selectedAccount()
              });
              this.currentPage.set(0);
              this.viewType.set(ViewType.UPLOAD_TRANSACTIONS);
              this.filesAreUploading.set(false);

              // Invalidate queries to refresh data
              this.queryClient.invalidateQueries({queryKey: ['transactions']});

              // Refresh manual review count
              const account = this.selectedAccount();
              if (account) {
                this.loadTransactionsToManuallyReviewCount(account);
              }

              this.snackBar.open('Transactions uploaded successfully', 'Close', {duration: 3000});
            }
          },
          error: (error) => {
            this.filesAreUploading.set(false);
            console.error('Upload error:', error);
            this.errorDialogService.openErrorDialog('Upload Failed',
                error.message || 'An error occurred during upload');
          }
        });

    // Reset file input
    this.fileInput.nativeElement.value = '';
  }

  openSearchDialog(): void {
    const dialogRef = this.dialog.open(TransactionSearchDialogComponent, {
      restoreFocus: false,
      width: '700px',
      maxWidth: '95vw',
      maxHeight: '90vh',
      panelClass: 'transaction-search-dialog-panel'
    });

    dialogRef.afterClosed()
        .pipe(takeUntilDestroyed(this.destroyRef))
        .subscribe(result => {
          if (!result) {
            return;
          }

          const query: TransactionQuery = {
            ...result,
            accountNumber: this.selectedAccount()
          };

          this.transactionQuery.set(query);
          this.currentPage.set(0);
          this.viewType.set(ViewType.RUN_QUERY);
        });
  }

  // Pagination handlers
  onPageChange(event: PageEvent): void {
    this.currentPage.set(event.pageIndex);
    this.pageSize.set(event.pageSize);
  }

  // Sort handler
  onSortChange(event: Sort): void {
    const propertyMap: Record<string, TransactionSortProperty> = {
      'bookingDate': 'booking_date' as TransactionSortProperty,
      'counterparty': 'counterparty' as TransactionSortProperty,
      'transaction': 'transaction' as TransactionSortProperty,
      'amount': 'amount' as TransactionSortProperty
    };

    const property = propertyMap[event.active] || 'booking_date' as TransactionSortProperty;
    const order = (event.direction || 'asc') as SortOrder;

    this.sortConfig.set({property, order});
  }

  // Transaction update handlers
  setCategory(transaction: TransactionWithCategory, selectedCategoryQualifiedNameStr: string): void {
    const index = this.categoryIndex();
    const category = index?.qualifiedNameToCategoryIndex[selectedCategoryQualifiedNameStr];
    if (!category) {
      this.snackBar.open('Category not found', 'Close', {duration: 3000});
      return;
    }

    const update: TransactionUpdate = {
      categoryId: category.id,
      manuallyAssignedCategory: true
    };

    this.saveTransactionMutation.mutate({
      transactionId: transaction.transactionId,
      update
    });
  }

  setIsRecurring(transaction: TransactionWithCategory, event: MatRadioChange): void {
    const update: TransactionUpdate = {
      isRecurring: event.value
    };

    this.saveTransactionMutation.mutate({
      transactionId: transaction.transactionId,
      update
    });
  }

  setIsAdvanceSharedAccount(transaction: TransactionWithCategory, event: MatRadioChange): void {
    const update: TransactionUpdate = {
      isAdvanceSharedAccount: event.value
    };

    this.saveTransactionMutation.mutate({
      transactionId: transaction.transactionId,
      update
    });
  }

  // Helper methods
  amountType(transaction: TransactionWithCategory): AmountType {
    if (transaction.amount === undefined || transaction.amount === null) {
      return AmountType.BOTH;
    }
    return inferAmountType(transaction.amount);
  }

  getCategoryQualifiedName(transaction: TransactionWithCategory): string | undefined {
    return transaction.category?.qualifiedName;
  }

  formatDate(dateStr: string | null | undefined): string {
    if (!dateStr) {
      return 'N/A';
    }
    try {
      const date = new Date(dateStr);
      return this.datePipe.transform(date, 'dd/MM/yyyy') || 'N/A';
    } catch {
      return 'N/A';
    }
  }

  getNrOfTransactionsToManuallyReview(): string {
    const count = this.transactionsToManuallyReview();
    return count > 0 ? count.toString() : '';
  }

  getNrOfTransactionsToManuallyReviewTooltip(): string {
    const count = this.transactionsToManuallyReview();
    return count > 0 ? `You have ${count} transactions to manually review` : 'No transactions to review';
  }
}
