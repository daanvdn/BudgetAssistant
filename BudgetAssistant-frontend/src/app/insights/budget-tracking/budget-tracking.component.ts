import {Component, computed, DestroyRef, effect, inject, input, signal} from '@angular/core';
import {DecimalPipe} from '@angular/common';
import {MatProgressSpinner} from '@angular/material/progress-spinner';
import {MatIcon} from '@angular/material/icon';
import {MatTooltip} from '@angular/material/tooltip';
import {
  BudgetAssistantApiService,
  BudgetEntryResult,
  BudgetTrackerResult,
  RecurrenceType,
  RevenueExpensesQuery,
  TransactionTypeEnum,
} from '@daanvdn/budget-assistant-client';
import {injectQuery} from '@tanstack/angular-query-experimental';
import {firstValueFrom} from 'rxjs';

import {Criteria} from '../../model';
import {DateUtilsService} from '../../shared/date-utils.service';
import {ErrorDialogService} from '../../error-dialog/error-dialog.service';

@Component({
  selector: 'budget-tracking',
  templateUrl: './budget-tracking.component.html',
  styleUrls: ['./budget-tracking.component.scss'],
  standalone: true,
  imports: [
    DecimalPipe,
    MatProgressSpinner,
    MatIcon,
    MatTooltip,
  ],
})
export class BudgetTrackingComponent {
  private readonly apiService = inject(BudgetAssistantApiService);
  private readonly dateUtilsService = inject(DateUtilsService);
  private readonly errorDialogService = inject(ErrorDialogService);

  /** Expose Math for template usage */
  protected readonly Math = Math;

  /** Signal-based input from parent (InsightsComponent) */
  criteria = input<Criteria>();

  /** Internal signal tracking the active criteria for the query key */
  private activeCriteria = signal<Criteria | undefined>(undefined);

  /** Sort state */
  sortColumn = signal<keyof BudgetEntryResult | ''>('');
  sortDirection = signal<'asc' | 'desc'>('asc');

  /** Use TanStack Query for caching and automatic state management */
  budgetQuery = injectQuery(() => ({
    queryKey: ['budgetTracking', this.queryKeyFromCriteria()],
    queryFn: (): Promise<BudgetTrackerResult | null> => {
      const criteria = this.activeCriteria();
      if (!criteria) {
        return Promise.resolve(null);
      }
      const query: RevenueExpensesQuery = {
        accountNumber: criteria.bankAccount.accountNumber,
        grouping: criteria.grouping,
        transactionType: TransactionTypeEnum.BOTH,
        start: this.dateUtilsService.stringifyDateWithoutTime(criteria.startDate),
        end: this.dateUtilsService.stringifyDateWithoutTime(criteria.endDate),
        expensesRecurrence: RecurrenceType.BOTH,
        revenueRecurrence: RecurrenceType.BOTH,
      };
      return firstValueFrom(
        this.apiService.analysis.trackBudgetApiAnalysisTrackBudgetPost(query)
      );
    },
    enabled: !!this.activeCriteria(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  }));

  /** Stable, serializable query key derived from criteria */
  private queryKeyFromCriteria = computed(() => {
    const c = this.activeCriteria();
    if (!c) return null;
    return {
      account: c.bankAccount.accountNumber,
      grouping: c.grouping,
      start: c.startDate?.toISOString(),
      end: c.endDate?.toISOString(),
    };
  });

  /** Sorted entries derived from the query result */
  sortedEntries = computed<BudgetEntryResult[]>(() => {
    const result = this.budgetQuery.data();
    if (!result?.entries) return [];
    const entries = [...result.entries];
    const col = this.sortColumn();
    const dir = this.sortDirection();
    if (!col) return entries;
    return entries.sort((a, b) => {
      const aVal = a[col] ?? 0;
      const bVal = b[col] ?? 0;
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return dir === 'asc' ? aVal - bVal : bVal - aVal;
      }
      const aStr = String(aVal);
      const bStr = String(bVal);
      return dir === 'asc' ? aStr.localeCompare(bStr) : bStr.localeCompare(aStr);
    });
  });

  /** Totals from the response */
  totalBudgeted = computed(() => this.budgetQuery.data()?.totalBudgeted ?? 0);
  totalActual = computed(() => this.budgetQuery.data()?.totalActual ?? 0);
  totalDifference = computed(() => this.budgetQuery.data()?.totalDifference ?? 0);
  period = computed(() => this.budgetQuery.data()?.period ?? '');
  startDate = computed(() => this.budgetQuery.data()?.startDate ?? '');
  endDate = computed(() => this.budgetQuery.data()?.endDate ?? '');

  /** Show error dialog on query failure */
  private errorEffect = effect(() => {
    const error = this.budgetQuery.error();
    if (error) {
      this.errorDialogService.openErrorDialog(
        'Failed to load budget tracking data',
        error instanceof Error ? error.message : String(error)
      );
    }
  });

  /** Watch for criteria changes and trigger query */
  private criteriaEffect = effect(() => {
    const c = this.criteria();
    if (c) {
      this.activeCriteria.set(c);
    }
  }, { allowSignalWrites: true });

  /** Toggle sort on a column */
  toggleSort(column: keyof BudgetEntryResult): void {
    if (this.sortColumn() === column) {
      this.sortDirection.set(this.sortDirection() === 'asc' ? 'desc' : 'asc');
    } else {
      this.sortColumn.set(column);
      this.sortDirection.set('asc');
    }
  }

  /** Get CSS class for difference values */
  getDifferenceClass(value: number | undefined): string {
    if (value === undefined || value === null) return '';
    return value >= 0 ? 'positive' : 'negative';
  }

  /** Get CSS class for percentage used */
  getPercentageClass(value: number | undefined): string {
    if (value === undefined || value === null) return '';
    if (value <= 80) return 'percentage-good';
    if (value <= 100) return 'percentage-warning';
    return 'percentage-over';
  }

  /** Get sort icon for a column */
  getSortIcon(column: keyof BudgetEntryResult): string {
    if (this.sortColumn() !== column) return 'unfold_more';
    return this.sortDirection() === 'asc' ? 'arrow_upward' : 'arrow_downward';
  }

  /** Format a number for display with 2 decimal places */
  formatAmount(value: number | undefined): string {
    if (value === undefined || value === null) return 'N/A';
    return value.toFixed(2);
  }
}
