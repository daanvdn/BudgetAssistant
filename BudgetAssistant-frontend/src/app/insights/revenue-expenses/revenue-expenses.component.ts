import {Component, computed, inject, input, OnInit, signal} from '@angular/core';
import {CommonModule, DecimalPipe} from '@angular/common';
import {MatTableModule} from '@angular/material/table';
import {MatButtonModule} from '@angular/material/button';
import {MatIconModule} from '@angular/material/icon';
import {MatProgressSpinnerModule} from '@angular/material/progress-spinner';
import {MatCardModule} from '@angular/material/card';
import {MatSnackBar, MatSnackBarModule} from '@angular/material/snack-bar';
import {BaseChartDirective} from 'ng2-charts';
import ChartDataLabels from 'chartjs-plugin-datalabels';
import {ChartConfiguration, ChartData} from 'chart.js';
import {injectQuery} from '@tanstack/angular-query-experimental';
import {firstValueFrom} from 'rxjs';

import {
  BudgetAssistantApiService,
  ExpensesAndRevenueForPeriod,
  RecurrenceType,
  RevenueExpensesQuery,
  TransactionTypeEnum
} from '@daanvdn/budget-assistant-client';
import {DateUtilsService} from "../../shared/date-utils.service";
import {Criteria} from "../../model";

/**
 * Extended interface to include computed balance for display
 */
interface ExpensesAndRevenueForPeriodWithBalance extends ExpensesAndRevenueForPeriod {
  balance: number;
}

@Component({
  selector: 'expenses-revenue',
  templateUrl: './revenue-expenses.component.html',
  styleUrls: ['./revenue-expenses.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    MatTableModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatCardModule,
    MatSnackBarModule,
    BaseChartDirective,
    DecimalPipe
  ]
})
export class ExpensesRevenueComponent implements OnInit {
  // Dependency injection
  private readonly apiService = inject(BudgetAssistantApiService);
  private readonly snackBar = inject(MatSnackBar);
  private readonly dateUtilsService = inject(DateUtilsService);

  // Input signal for criteria (optional since parent may not initialize immediately)
  readonly criteria = input<Criteria | undefined>(undefined);

  // UI state signals
  protected readonly tableIsVisible = signal(false);

  // Table configuration
  protected readonly displayedColumns = ['period', 'revenue', 'expenses', 'balance'];

  // Chart plugins
  protected readonly chartPlugins = [ChartDataLabels];

  // Chart options
  protected readonly chartOptions: ChartConfiguration['options'] = {
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      datalabels: {
        display: true,
        align: 'end',
        anchor: 'end',
        formatter: (value: number) => value ? Math.round(value) : null,
        font: {
          weight: 'bold',
          size: 11
        }
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        callbacks: {
          label: (context) => {
            const label = context.dataset.label || '';
            const value = context.raw as number;
            return `${label}: €${value.toLocaleString('nl-NL', {minimumFractionDigits: 2})}`;
          }
        }
      },
      legend: {
        position: 'top',
        labels: {
          usePointStyle: true,
          padding: 20
        }
      }
    },
    scales: {
      x: {
        beginAtZero: true,
        ticks: {
          callback: (value) => `€${value.toLocaleString('nl-NL')}`
        }
      },
      y: {
        ticks: {
          font: {
            size: 12
          }
        }
      }
    }
  };

  // TanStack Query for revenue/expenses data
  revenueExpensesQuery = injectQuery(() => {
    const currentCriteria = this.criteria();
    
    return {
      queryKey: ['revenueExpenses', currentCriteria?.bankAccount?.accountNumber, currentCriteria?.grouping, currentCriteria?.startDate?.toISOString(), currentCriteria?.endDate?.toISOString()],
      queryFn: async () => {
        // Safe to assert non-null since query is only enabled when criteria is valid
        const query = this.buildQuery(currentCriteria!);
        const response = await firstValueFrom(
          this.apiService.analysis.getRevenueAndExpensesPerPeriodApiAnalysisRevenueExpensesPerPeriodPost(query)
        );
        return response.content;
      },
      enabled: this.isValidCriteria(currentCriteria),
      staleTime: 30_000,
    };
  });

  // Computed signals for template
  protected readonly isWaitingForCriteria = computed(() => !this.isValidCriteria(this.criteria()));
  
  protected readonly isLoading = computed(() => this.revenueExpensesQuery.isPending() && !this.isWaitingForCriteria());
  
  protected readonly hasError = computed(() => this.revenueExpensesQuery.isError());
  
  protected readonly errorMessage = computed(() => {
    const error = this.revenueExpensesQuery.error();
    return error instanceof Error ? error.message : 'An error occurred while loading data';
  });

  protected readonly data = computed<ExpensesAndRevenueForPeriodWithBalance[]>(() => {
    const rawData = this.revenueExpensesQuery.data();
    if (!rawData) return [];
    
    return rawData.map(item => ({
      ...item,
      balance: (item.revenue ?? 0) - Math.abs(item.expenses ?? 0)
    }));
  });

  protected readonly hasData = computed(() => this.data().length > 0);
  
  protected readonly isEmpty = computed(() => !this.isLoading() && !this.hasError() && !this.hasData());

  // Chart data computed from API response
  protected readonly chartData = computed<ChartData<'bar'>>(() => {
    const items = this.data();
    
    return {
      labels: items.map(item => item.period),
      datasets: [
        {
          type: 'bar' as const,
          label: 'Revenue',
          backgroundColor: '#059669', // emerald-600
          borderColor: '#047857', // emerald-700
          borderWidth: 1,
          borderRadius: 4,
          data: items.map(item => item.revenue ?? 0)
        },
        {
          type: 'bar' as const,
          label: 'Expenses',
          backgroundColor: '#dc2626', // red-600
          borderColor: '#b91c1c', // red-700
          borderWidth: 1,
          borderRadius: 4,
          data: items.map(item => Math.abs(item.expenses ?? 0))
        }
      ]
    };
  });

  // Computed dynamic chart height based on data
  protected readonly chartHeight = computed(() => {
    const itemCount = this.data().length;
    const minHeight = 300;
    const heightPerItem = 50;
    return Math.max(minHeight, itemCount * heightPerItem);
  });

  ngOnInit(): void {
    // Query is automatically triggered when criteria input changes
  }

  // UI actions
  toggleTable(): void {
    this.tableIsVisible.update(visible => !visible);
  }

  protected get toggleTableLabel(): string {
    return this.tableIsVisible() ? 'Hide Table' : 'Show Table';
  }

  protected get toggleTableIcon(): string {
    return this.tableIsVisible() ? 'visibility_off' : 'visibility';
  }

  // Retry on error
  retry(): void {
    this.revenueExpensesQuery.refetch();
  }

  // Helper methods
  private buildQuery(criteria: Criteria): RevenueExpensesQuery {
    return {
      accountNumber: criteria.bankAccount.accountNumber,
      grouping: criteria.grouping,
      transactionType: TransactionTypeEnum.BOTH,
      start:  this.dateUtilsService.stringifyDateWithoutTime(criteria.startDate),
      end: this.dateUtilsService.stringifyDateWithoutTime(criteria.endDate),
      expensesRecurrence: RecurrenceType.BOTH,
      revenueRecurrence: RecurrenceType.BOTH
    };
  }



  private isValidCriteria(criteria: Criteria | undefined): boolean {
    return !!(
      criteria &&
      criteria.bankAccount?.accountNumber &&
      criteria.grouping &&
      criteria.startDate &&
      criteria.endDate
    );
  }

  // Balance formatting helper for template
  getBalanceClass(balance: number): string {
    return balance >= 0 ? 'positive' : 'negative';
  }
}
