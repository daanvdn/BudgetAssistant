import {Component, computed, DestroyRef, inject, OnInit, signal} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {CommonModule} from '@angular/common';
import {MatToolbar} from '@angular/material/toolbar';
import {MatButtonToggle, MatButtonToggleChange, MatButtonToggleGroup} from '@angular/material/button-toggle';
import {MatPaginator, PageEvent} from '@angular/material/paginator';
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
import {MatProgressSpinner} from '@angular/material/progress-spinner';
import {MatSnackBar, MatSnackBarModule} from '@angular/material/snack-bar';
import {MatIcon} from '@angular/material/icon';
import {MatCard, MatCardContent} from '@angular/material/card';
import {
  BudgetAssistantApiService,
  CategoryIndex,
  PageUncategorizedTransactionsRequest,
  SortOrder,
  TransactionRead,
  TransactionSortProperty,
  TransactionTypeEnum,
  TransactionUpdate
} from '@daanvdn/budget-assistant-client';
import {injectMutation, injectQuery, injectQueryClient} from '@tanstack/angular-query-experimental';
import {firstValueFrom} from 'rxjs';

import {AppService} from '../../app.service';
import {AmountType, inferAmountType} from '../../model';
import {BankAccountSelectionComponent} from '../../bank-account-selection/bank-account-selection.component';
import {CategoryTreeDropdownComponent} from '../../category-tree-dropdown/category-tree-dropdown.component';
import {BreakpointService} from '../../shared/breakpoint.service';

/** Represents a group header row in the table */
interface GroupHeaderRow {
  kind: 'group';
  counterpartyName: string;
  transactions: TransactionRead[];
  isExpense: boolean;
}

/** Union type for table rows */
type TableRow = (TransactionRead & { kind?: 'transaction' }) | GroupHeaderRow;

function isGroupRow(row: TableRow): row is GroupHeaderRow {
  return (row as GroupHeaderRow).kind === 'group';
}

@Component({
  selector: 'uncategorized-transactions',
  templateUrl: './uncategorized-transactions.component.html',
  styleUrls: ['./uncategorized-transactions.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    MatToolbar,
    MatButtonToggleGroup,
    MatButtonToggle,
    MatPaginator,
    MatTable,
    MatColumnDef,
    MatHeaderCellDef,
    MatHeaderCell,
    MatCellDef,
    MatCell,
    MatHeaderRowDef,
    MatHeaderRow,
    MatRowDef,
    MatRow,
    MatProgressSpinner,
    MatSnackBarModule,
    MatIcon,
    MatCard,
    MatCardContent,
    BankAccountSelectionComponent,
    CategoryTreeDropdownComponent
  ]
})
export class UncategorizedTransactionsComponent implements OnInit {
  // Dependency injection
  private readonly destroyRef = inject(DestroyRef);
  private readonly appService = inject(AppService);
  private readonly apiService = inject(BudgetAssistantApiService);
  private readonly snackBar = inject(MatSnackBar);
  private readonly queryClient = injectQueryClient();
  protected readonly breakpointService = inject(BreakpointService);

  // Signals
  protected readonly activeView = signal<TransactionTypeEnum>(TransactionTypeEnum.EXPENSES);
  protected readonly selectedAccount = signal<string | undefined>(undefined);
  protected readonly categoryIndex = signal<CategoryIndex | undefined>(undefined);
  protected readonly currentPage = signal(0);
  protected readonly pageSize = signal(50);
  protected readonly totalToReview = signal(0);

  // Table columns
  protected readonly displayedColumns = ['transaction', 'amount', 'category'];

  // TanStack Query – fetch uncategorized transactions
  transactionsQuery = injectQuery(() => ({
    queryKey: [
      'manualReviewTransactions',
      this.selectedAccount(),
      this.activeView(),
      this.currentPage(),
      this.pageSize()
    ],
    queryFn: async () => {
      const account = this.selectedAccount();
      if (!account) throw new Error('No bank account selected');

      const request: PageUncategorizedTransactionsRequest = {
        page: this.currentPage(),
        size: this.pageSize(),
        sortOrder: 'asc' as SortOrder,
        sortProperty: 'counterparty' as TransactionSortProperty,
        bankAccount: account,
        transactionType: this.activeView()
      };

      return firstValueFrom(
        this.apiService.transactions.pageUncategorizedTransactionsApiTransactionsPageUncategorizedPost(request)
      );
    },
    enabled: !!this.selectedAccount(),
    staleTime: 5 * 60_000,
  }));

  // Save-transaction mutation
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
      // Invalidate to refresh the list (transaction may leave the "to review" set)
      this.queryClient.invalidateQueries({ queryKey: ['manualReviewTransactions', this.selectedAccount(), this.activeView()] });
      this.refreshCount();
    },
    onError: (error: any) => {
      console.error('Error saving transaction:', error);
      this.snackBar.open('Failed to save transaction', 'Close', { duration: 3000 });
    }
  }));

  // Computed: grouped table rows
  protected readonly tableRows = computed<TableRow[]>(() => {
    const data = this.transactionsQuery.data();
    if (!data?.content?.length) return [];

    const isExpense = this.activeView() === TransactionTypeEnum.EXPENSES;
    const grouped = new Map<string, TransactionRead[]>();

    for (const tx of data.content) {
      const name = tx.counterparty?.name || '';
      if (!grouped.has(name)) grouped.set(name, []);
      grouped.get(name)!.push(tx);
    }

    const sortedKeys = [...grouped.keys()].sort((a, b) => a.localeCompare(b));
    const rows: TableRow[] = [];

    for (const key of sortedKeys) {
      const transactions = grouped.get(key)!;
      rows.push({ kind: 'group', counterpartyName: key, transactions, isExpense });
      rows.push(...transactions.map(tx => ({ ...tx, kind: 'transaction' as const })));
    }

    return rows;
  });

  // Computed: mobile-friendly grouped data
  protected readonly groupedTransactions = computed(() => {
    const data = this.transactionsQuery.data();
    if (!data?.content?.length) return [];

    const isExpense = this.activeView() === TransactionTypeEnum.EXPENSES;
    const grouped = new Map<string, TransactionRead[]>();

    for (const tx of data.content) {
      const name = tx.counterparty?.name || '';
      if (!grouped.has(name)) grouped.set(name, []);
      grouped.get(name)!.push(tx);
    }

    return [...grouped.entries()]
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([name, transactions]) => ({ name, transactions, isExpense }));
  });

  // Computed: pagination
  protected readonly pagination = computed(() => {
    const data = this.transactionsQuery.data();
    return {
      page: data?.page ?? 0,
      size: data?.size ?? this.pageSize(),
      totalElements: data?.totalElements ?? 0,
      totalPages: data?.totalPages ?? 0
    };
  });

  protected readonly isLoading = computed(() => this.transactionsQuery.isPending());
  protected readonly isEmpty = computed(() =>
    !this.isLoading() && (this.transactionsQuery.data()?.content?.length ?? 0) === 0 && !!this.selectedAccount()
  );

  ngOnInit(): void {
    // Subscribe to category index
    this.appService.categoryIndexObservable$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(index => this.categoryIndex.set(index));

    // Subscribe to bank account changes
    this.appService.selectedBankAccountObservable$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(account => {
        if (account?.accountNumber) {
          this.selectedAccount.set(account.accountNumber);
          this.currentPage.set(0);
          this.refreshCount();
        }
      });
  }

  /** Refresh the count of transactions awaiting manual review */
  private refreshCount(): void {
    const account = this.selectedAccount();
    if (!account) return;
    this.appService.countUncategorizedTransactions(account)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: count => this.totalToReview.set(count.valueOf()),
        error: () => this.totalToReview.set(0)
      });
  }

  // --- Event Handlers ---

  onToggleChange(event: MatButtonToggleChange): void {
    const value = event.value;
    this.activeView.set(value === 'revenue' ? TransactionTypeEnum.REVENUE : TransactionTypeEnum.EXPENSES);
    this.currentPage.set(0);
  }

  onPageChange(event: PageEvent): void {
    this.currentPage.set(event.pageIndex);
    this.pageSize.set(event.pageSize);
  }

  /** Assign a category — works for both single transactions and group headers */
  setCategory(row: TableRow, selectedCategoryQualifiedName: string): void {
    const index = this.categoryIndex();
    const category = index?.qualifiedNameToCategoryIndex[selectedCategoryQualifiedName];
    if (!category) {
      this.snackBar.open('Category not found', 'Close', { duration: 3000 });
      return;
    }

    if (isGroupRow(row)) {
      // Bulk assign for all transactions in the group
      const count = row.transactions.length;
      for (const tx of row.transactions) {
        this.saveTransactionMutation.mutate({
          transactionId: tx.transactionId,
          update: { categoryId: category.id,
            manuallyAssignedCategory: true,
            isManuallyReviewed : true

          }
        });
      }
      this.snackBar.open(`Category assigned to ${count} transaction(s)`, 'Close', { duration: 2000 });
    } else {
      this.saveTransactionMutation.mutate({
        transactionId: row.transactionId,
        update: {
          categoryId: category.id,
          manuallyAssignedCategory: true,
          isManuallyReviewed : true
        }
      });
      this.snackBar.open('Category saved', 'Close', { duration: 2000 });
    }
  }

  /** Determine AmountType for category dropdown filtering */
  amountType(row: TableRow): AmountType {
    if (isGroupRow(row)) {
      return row.isExpense ? AmountType.EXPENSES : AmountType.REVENUE;
    }
    if (row.amount == null) return AmountType.BOTH;
    return inferAmountType(row.amount);
  }

  /** Get category qualified name for pre-selecting the dropdown */
  getCategoryQualifiedName(row: TableRow): string | undefined {
    if (isGroupRow(row)) return undefined;
    const index = this.categoryIndex();
    if (!index || row.categoryId == null) return undefined;
    const cat = index.idToCategoryIndex[row.categoryId];
    return cat?.qualifiedName;
  }

  /** MatTable predicate: is this row a group header? */
  isGroup = (_index: number, item: TableRow): boolean => isGroupRow(item);

  /** MatTable predicate: is this row a transaction? */
  isTransaction = (_index: number, item: TableRow): boolean => !isGroupRow(item);

  /** Track by for mobile @for */
  protected trackByCounterparty = (_index: number, group: { name: string }) => group.name;
}
