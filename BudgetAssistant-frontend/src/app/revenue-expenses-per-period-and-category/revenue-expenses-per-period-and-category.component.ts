import { Component, computed, effect, inject, input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatDialog } from '@angular/material/dialog';
import { MatTableModule } from '@angular/material/table';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { CdkMenuModule } from '@angular/cdk/menu';
import { ChartModule } from 'primeng/chart';
import ChartDataLabels from 'chartjs-plugin-datalabels';
// @ts-ignore
import autocolors from 'chartjs-plugin-autocolors';
import { injectQuery } from '@tanstack/angular-query-experimental';
import { firstValueFrom } from 'rxjs';

import { Criteria } from '../model/criteria.model';
import { AppService } from '../app.service';
import {
  BudgetAssistantApiService,
  CategoryAmount,
  PeriodCategoryBreakdown,
  RecurrenceType,
  RevenueAndExpensesPerPeriodAndCategory,
  RevenueExpensesQuery,
  TransactionInContextQuery,
  TransactionTypeEnum
} from '@daanvdn/budget-assistant-client';
import { TransactionsInContextDialogComponent } from '../transaction-dialog/transactions-in-context-dialog.component';
import { ErrorDialogService } from '../error-dialog/error-dialog.service';

/**
 * Represents a single row in the category breakdown table.
 * Dynamic keys are period names (e.g., "2024-Q1") with { value, isAnomaly } objects.
 */
interface TableRow {
  category: string;
  categoryId?: number;
  [periodKey: string]: string | number | { value: number; isAnomaly: boolean } | undefined;
}

/**
 * Chart data structure for Chart.js
 */
interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    maxBarThickness?: number;
  }[];
}

@Component({
  selector: 'revenue-expenses-per-period-and-category',
  templateUrl: './revenue-expenses-per-period-and-category.component.html',
  styleUrls: ['./revenue-expenses-per-period-and-category.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    ChartModule,
    MatTableModule,
    MatTooltipModule,
    MatProgressSpinnerModule,
    MatIconModule,
    MatCardModule,
    CdkMenuModule
  ]
})
export class RevenueExpensesPerPeriodAndCategoryComponent {
  // Injected dependencies
  private readonly apiService = inject(BudgetAssistantApiService);
  private readonly appService = inject(AppService);
  private readonly dialog = inject(MatDialog);
  private readonly errorDialogService = inject(ErrorDialogService);

  // Input
  readonly criteria = input<Criteria>();

  // Chart configuration
  readonly chartPlugins = [ChartDataLabels, autocolors];
  readonly chartOptions = this.initChartOptions();

  // State signals
  readonly currentContextQuery = signal<TransactionInContextQuery | null>(null);

  // Query for fetching data
  readonly dataQuery = injectQuery(() => ({
    queryKey: ['revenueExpensesPerPeriodAndCategory', this.getCriteriaKey()],
    queryFn: () => this.fetchData(),
    enabled: !!this.criteria(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  }));

  // Computed values from query result
  readonly chartData = computed<ChartData | null>(() => {
    const data = this.dataQuery.data();
    if (!data) return null;
    return this.transformToChartData(data.periods ?? [], data.allCategories ?? []);
  });

  readonly tableData = computed<TableRow[]>(() => {
    const data = this.dataQuery.data();
    if (!data) return [];
    return this.transformToTableData(data.periods ?? [], data.allCategories ?? []);
  });

  readonly displayedColumns = computed<string[]>(() => {
    const data = this.dataQuery.data();
    if (!data?.periods?.length) return ['category'];
    return ['category', ...data.periods.map(p => p.period)];
  });

  readonly periodColumns = computed<string[]>(() => {
    return this.displayedColumns().slice(1);
  });

  readonly isLoading = computed(() => this.dataQuery.isPending());
  readonly hasError = computed(() => this.dataQuery.isError());
  readonly isEmpty = computed(() => !this.isLoading() && this.tableData().length === 0);
  readonly hasData = computed(() => this.tableData().length > 0);

  // Tooltip text
  readonly tableInfoTooltip = 'This table shows the breakdown of amounts per category for each period. ' +
    'Cells highlighted in red indicate unusually high values (potential anomalies). ' +
    'Right-click on any cell to view the underlying transactions.';

  protected readonly TransactionTypeEnum = TransactionTypeEnum;

  constructor() {
    // Log errors when query fails
    effect(() => {
      const error = this.dataQuery.error();
      if (error) {
        console.error('Failed to fetch revenue/expenses data:', error);
      }
    });
  }

  /**
   * Generate a unique key for the current criteria to use in query caching
   */
  private getCriteriaKey(): string {
    const c = this.criteria();
    if (!c) return 'none';
    return `${c.bankAccount?.accountNumber}-${c.grouping}-${c.startDate?.toISOString()}-${c.endDate?.toISOString()}-${c.transactionType}`;
  }

  /**
   * Fetch data from the API
   */
  private async fetchData(): Promise<RevenueAndExpensesPerPeriodAndCategory> {
    const c = this.criteria();
    if (!c) {
      throw new Error('Criteria is required');
    }

    const query: RevenueExpensesQuery = {
      accountNumber: c.bankAccount.accountNumber,
      grouping: c.grouping,
      transactionType: TransactionTypeEnum.BOTH,
      start: JSON.stringify(c.startDate),
      end: JSON.stringify(c.endDate),
      expensesRecurrence: RecurrenceType.BOTH,
      revenueRecurrence: RecurrenceType.BOTH
    };

    return firstValueFrom(
      this.apiService.analysis.getRevenueAndExpensesPerPeriodAndCategoryApiAnalysisRevenueExpensesPerPeriodAndCategoryPost(query)
    );
  }

  /**
   * Initialize chart options for stacked horizontal bar chart
   */
  private initChartOptions(): any {
    return {
      plugins: {
        datalabels: {
          display: false,
          align: 'end',
          anchor: 'end',
          formatter: Math.round
        },
        autocolors: {
          enabled: true,
          mode: 'dataset'
        },
        legend: {
          position: 'bottom',
          labels: {
            usePointStyle: true,
            padding: 16,
            font: {
              size: 11
            }
          }
        },
        tooltip: {
          callbacks: {
            label: (context: any) => {
              const label = context.dataset.label || '';
              const value = context.parsed.x || 0;
              return `${label}: €${Math.abs(value).toLocaleString('nl-BE', { minimumFractionDigits: 2 })}`;
            }
          }
        }
      },
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          stacked: true,
          grid: {
            color: 'rgba(0, 0, 0, 0.05)'
          },
          ticks: {
            callback: (value: number) => '€' + Math.abs(value).toLocaleString('nl-BE')
          }
        },
        y: {
          stacked: true,
          grid: {
            display: false
          }
        }
      }
    };
  }

  /**
   * Transform API response to chart data format
   */
  private transformToChartData(periods: PeriodCategoryBreakdown[], allCategories: string[]): ChartData {
    const labels = periods.map(p => p.period);
    const datasets = allCategories.map(category => ({
      label: category,
      data: periods.map(periodData => {
        const categoryData = (periodData.categories ?? []).find(
          (cat: CategoryAmount) => cat.categoryQualifiedName === category
        );
        return Math.abs(categoryData?.amount ?? 0);
      }),
      maxBarThickness: 40
    }));

    return { labels, datasets };
  }

  /**
   * Transform API response to table data format with anomaly detection
   */
  private transformToTableData(periods: PeriodCategoryBreakdown[], allCategories: string[]): TableRow[] {
    // Calculate statistics for anomaly detection (values > 2 standard deviations from mean)
    const categoryStats = this.calculateCategoryStats(periods, allCategories);

    return allCategories.map(category => {
      // Look up the category ID using the AppService
      const categoryId = this.appService.getCategoryIdByQualifiedName(category);
      const row: TableRow = { category, categoryId };
      const stats = categoryStats.get(category);

      periods.forEach(period => {
        const categoryData = (period.categories ?? []).find(
          (c: CategoryAmount) => c.categoryQualifiedName === category
        );
        const amount = categoryData?.amount ?? 0;
        const absAmount = Math.abs(amount);

        // Check for anomaly (value > mean + 2*stdDev)
        let isAnomaly = false;
        if (stats && stats.stdDev > 0) {
          isAnomaly = absAmount > stats.mean + 2 * stats.stdDev;
        }

        row[period.period] = {
          value: amount,
          isAnomaly
        };
      });

      return row;
    });
  }

  /**
   * Calculate mean and standard deviation for each category's values
   */
  private calculateCategoryStats(periods: PeriodCategoryBreakdown[], allCategories: string[]): Map<string, { mean: number; stdDev: number }> {
    const stats = new Map<string, { mean: number; stdDev: number }>();

    allCategories.forEach(category => {
      const values = periods.map(period => {
        const categoryData = (period.categories ?? []).find(
          (c: CategoryAmount) => c.categoryQualifiedName === category
        );
        return Math.abs(categoryData?.amount ?? 0);
      }).filter(v => v > 0);

      if (values.length > 1) {
        const mean = values.reduce((a, b) => a + b, 0) / values.length;
        const variance = values.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / values.length;
        const stdDev = Math.sqrt(variance);
        stats.set(category, { mean, stdDev });
      } else {
        stats.set(category, { mean: values[0] || 0, stdDev: 0 });
      }
    });

    return stats;
  }

  /**
   * Get cell value for display in table
   */
  getCellValue(element: TableRow, column: string): number {
    const cell = element[column];
    if (typeof cell === 'object' && cell !== null && 'value' in cell) {
      return cell.value;
    }
    return typeof cell === 'number' ? cell : 0;
  }

  /**
   * Check if a cell contains an anomaly
   */
  isAnomaly(element: TableRow, column: string): boolean {
    const cell = element[column];
    if (typeof cell === 'object' && cell !== null && 'isAnomaly' in cell) {
      return cell.isAnomaly;
    }
    return false;
  }

  /**
   * Format amount for display
   */
  formatAmount(amount: number): string {
    return new Intl.NumberFormat('nl-BE', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 2
    }).format(amount);
  }

  /**
   * Handle context menu open for a table cell
   */
  openContextMenu(period: string, category: string, categoryId: number | undefined, event: MouseEvent): void {
    event.preventDefault();

    const c = this.criteria();
    if (!c) return;

    this.currentContextQuery.set({
      period: period,
      categoryId: categoryId ?? 0,
      bankAccount: c.bankAccount.accountNumber,
      transactionType: c.transactionType as TransactionTypeEnum
    });
  }

  /**
   * Open dialog to show transactions for the current context
   */
  onShowTransactions(): void {
    const query = this.currentContextQuery();
    if (!query) return;

    this.dialog.open(TransactionsInContextDialogComponent, {
      data: query,
      width: '90vw',
      maxWidth: '1200px',
      maxHeight: '80vh'
    });
  }

  /**
   * Handle chart data point selection
   */
  handleDataSelect(event: any): void {
    console.log('Chart data selected:', event);
    // Future enhancement: could open transaction dialog for selected data point
  }
}
