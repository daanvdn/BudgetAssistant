import {CommonModule, DatePipe, TitleCasePipe} from '@angular/common';
import {Component, computed, DestroyRef, inject, OnInit, signal} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {
  MAT_DIALOG_DATA,
  MatDialogActions,
  MatDialogContent,
  MatDialogRef,
  MatDialogTitle
} from '@angular/material/dialog';
import {MatButton} from '@angular/material/button';
import {MatPaginator, PageEvent} from '@angular/material/paginator';
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
import {MatProgressSpinner} from '@angular/material/progress-spinner';
import {MatIcon} from '@angular/material/icon';
import {MatSnackBar, MatSnackBarModule} from '@angular/material/snack-bar';
import {MatCard, MatCardContent} from '@angular/material/card';

import {
  BudgetAssistantApiService,
  CategoryIndex,
  CategoryRead,
  PageTransactionsInContextRequest,
  SortOrder,
  TransactionInContextQuery,
  TransactionSortProperty,
  TransactionUpdate
} from '@daanvdn/budget-assistant-client';
import {injectMutation, injectQuery} from '@tanstack/angular-query-experimental';
import {firstValueFrom} from 'rxjs';

import {AppService} from '../app.service';
import {AmountType, inferAmountType, TransactionWithCategory} from '../model';
import {CategoryTreeDropdownComponent} from '../category-tree-dropdown/category-tree-dropdown.component';
import {BreakpointService} from '../shared/breakpoint.service';

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
  selector: 'transactions-in-context-dialog',
  templateUrl: './transactions-in-context-dialog.component.html',
  styleUrls: ['./transactions-in-context-dialog.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    MatDialogTitle,
    MatDialogContent,
    MatDialogActions,
    MatButton,
    MatTable,
    MatSort,
    MatColumnDef,
    MatHeaderCellDef,
    MatHeaderCell,
    MatSortHeader,
    MatCellDef,
    MatCell,
    MatHeaderRowDef,
    MatHeaderRow,
    MatRowDef,
    MatRow,
    MatPaginator,
    MatProgressSpinner,
    MatIcon,
    MatSnackBarModule,
    MatCard,
    MatCardContent,
    CategoryTreeDropdownComponent,
    TitleCasePipe,
  ],
  providers: [DatePipe]
})
export class TransactionsInContextDialogComponent implements OnInit {
  // Dependency injection
  private readonly destroyRef = inject(DestroyRef);
  private readonly appService = inject(AppService);
  private readonly apiService = inject(BudgetAssistantApiService);
  private readonly dialogRef = inject(MatDialogRef<TransactionsInContextDialogComponent>);
  private readonly datePipe = inject(DatePipe);
  protected readonly breakpointService = inject(BreakpointService);
  private readonly snackBar = inject(MatSnackBar);
  readonly query: TransactionInContextQuery = inject(MAT_DIALOG_DATA);

  // Signals for state management
  protected readonly categoryIndex = signal<CategoryIndex | undefined>(undefined);
  protected readonly currentPage = signal(0);
  protected readonly pageSize = signal(50);
  protected readonly sortConfig = signal<SortConfig>({
    property: 'booking_date' as TransactionSortProperty,
    order: 'desc' as SortOrder
  });

  // Displayed columns (same set as original — no additional properties)
  protected readonly displayedColumns = [
    'bookingDate',
    'counterparty',
    'transaction',
    'amount',
    'transactionType'
  ];

  // Computed: whether category index is ready
  private readonly isCategoryIndexReady = computed(() => {
    const index = this.categoryIndex();
    return index !== undefined && Object.keys(index.idToCategoryIndex).length > 0;
  });

  // Computed: resolve the category name for the dialog title
  protected readonly categoryName = computed(() => {
    const index = this.categoryIndex();
    if (!index) return `Category #${this.query.categoryId}`;
    const cat: CategoryRead | undefined = index.idToCategoryIndex[this.query.categoryId];
    return cat?.qualifiedName ?? cat?.name ?? `Category #${this.query.categoryId}`;
  });

  // TanStack Query for paginated transactions
  transactionsQuery = injectQuery(() => ({
    queryKey: [
      'transactions-in-context',
      this.query.categoryId,
      this.query.period,
      this.query.bankAccount,
      this.currentPage(),
      this.pageSize(),
      this.sortConfig()
    ],
    queryFn: async () => {
      const request: PageTransactionsInContextRequest = {
        page: this.currentPage(),
        size: this.pageSize(),
        sortOrder: this.sortConfig().order,
        sortProperty: this.sortConfig().property,
        query: this.query
      };

      const result = await firstValueFrom(
        this.apiService.transactions.pageTransactionsInContextApiTransactionsPageInContextPost(request)
      );

      return {
        ...result,
        content: this.appService.mapTransactionsWithCategory(result.content)
      };
    },
    enabled: this.isCategoryIndexReady(),
    staleTime: 30_000,
  }));

  // Computed template helpers
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
    return this.transactionsQuery.isPending();
  });

  protected readonly isEmpty = computed(() => {
    return !this.isLoading() && this.transactions().length === 0;
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
    this.appService.categoryIndexObservable$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(categoryIndex => {
        this.categoryIndex.set(categoryIndex);
      });
  }

  // Event handlers
  onSortChange(event: Sort): void {
    const propertyMap: Record<string, TransactionSortProperty> = {
      'bookingDate': 'booking_date' as TransactionSortProperty,
      'counterparty': 'counterparty' as TransactionSortProperty,
      'transaction': 'transaction' as TransactionSortProperty,
      'amount': 'amount' as TransactionSortProperty
    };

    const property = propertyMap[event.active] || 'booking_date' as TransactionSortProperty;
    const order = (event.direction || 'desc') as SortOrder;
    this.sortConfig.set({property, order});
  }

  onPageChange(event: PageEvent): void {
    this.currentPage.set(event.pageIndex);
    this.pageSize.set(event.pageSize);
  }

  setCategory(transaction: TransactionWithCategory, selectedCategoryQualifiedNameStr: string): void {
    const index = this.categoryIndex();
    const category = index?.qualifiedNameToCategoryIndex[selectedCategoryQualifiedNameStr];
    if (!category) {
      this.snackBar.open('Category not found', 'Close', {duration: 3000});
      return;
    }

    const update: TransactionUpdate = {
      categoryId: category.id,
      manuallyAssignedCategory: true,
      isManuallyReviewed: true
    };

    this.saveTransactionMutation.mutate({
      transactionId: transaction.transactionId,
      update
    });
  }

  getCategoryQualifiedName(transaction: TransactionWithCategory): string | undefined {
    return transaction.category?.qualifiedName;
  }

  amountType(transaction: TransactionWithCategory): AmountType {
    if (transaction.amount === undefined || transaction.amount === null) {
      return AmountType.BOTH;
    }
    return inferAmountType(transaction.amount);
  }

  formatDate(dateStr: string | null | undefined): string {
    if (!dateStr) return 'N/A';
    try {
      const date = new Date(dateStr);
      return this.datePipe.transform(date, 'dd/MM/yyyy') || 'N/A';
    } catch {
      return 'N/A';
    }
  }

  onCloseClick(): void {
    this.dialogRef.close();
  }
}
