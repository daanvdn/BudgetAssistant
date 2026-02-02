import {Component, Input, OnChanges, OnInit, SimpleChanges, ViewChild} from '@angular/core';
import ChartDataLabels from 'chartjs-plugin-datalabels';

import {AppService} from '../app.service';
import {CategoryMap, DistributionByCategoryForPeriodTableData} from '../model';
import {Criteria} from "../model/criteria.model";
// @ts-ignore
import autocolors from 'chartjs-plugin-autocolors';
import { MatTable, MatTableDataSource, MatColumnDef, MatHeaderCellDef, MatHeaderCell, MatCellDef, MatCell, MatHeaderRowDef, MatHeaderRow, MatRowDef, MatRow } from "@angular/material/table";
import {MatDialog} from "@angular/material/dialog";
import {TransactionsInContextDialogComponent} from "../transaction-dialog/transactions-in-context-dialog.component";
import {
  BudgetAssistantApiService,
  CategoryAmount,
  PeriodCategoryBreakdown,
  RecurrenceType,
  RevenueAndExpensesPerPeriodAndCategory,
  RevenueExpensesQuery,
  TransactionInContextQuery,
  TransactionTypeEnum
} from "@daanvdn/budget-assistant-client";
import { NgIf, NgFor, NgClass } from '@angular/common';
import { CdkMenu, CdkMenuItem, CdkContextMenuTrigger } from '@angular/cdk/menu';
import { ChartModule } from 'primeng/chart';
import { MatTooltip } from '@angular/material/tooltip';

@Component({
    selector: 'revenue-expenses-per-period-and-category',
    templateUrl: './revenue-expenses-per-period-and-category.component.html',
    styleUrls: ['./revenue-expenses-per-period-and-category.component.scss'],
    standalone: true,
    imports: [NgIf, CdkMenu, CdkMenuItem, ChartModule, MatTooltip, MatTable, MatColumnDef, MatHeaderCellDef, MatHeaderCell, MatCellDef, MatCell, NgFor, NgClass, CdkContextMenuTrigger, MatHeaderRowDef, MatHeaderRow, MatRowDef, MatRow]
})
export class RevenueExpensesPerPeriodAndCategoryComponent implements OnInit, OnChanges {


  dummyIsLoaded = false
  //chart stuff
  datatIsLoaded: Boolean = false;
  chartOptions: any = this.initChartOptions();
  expensesData!: any;
  revenueData!: any;
  plugins: any[] = [ChartDataLabels, autocolors];
  @Input() criteria!: Criteria

  //table stuff
  @ViewChild(MatTable) table!: MatTable<DistributionByCategoryForPeriodTableData>;
  expensesDataSource!: MatTableDataSource<DistributionByCategoryForPeriodTableData>;
  expensesDataSourceAll!: MatTableDataSource<DistributionByCategoryForPeriodTableData>;
  revenueDataSource!: MatTableDataSource<DistributionByCategoryForPeriodTableData>;
  revenueDataSourceAll!: MatTableDataSource<DistributionByCategoryForPeriodTableData>;
  displayedColumns!: string[];
  displayedColumnsExceptFirst!: string[];
  firstColumn!: string;
  anomaliesToolTip: string = "Anomalies are transactions that are significantly different from the average amount" +
      " for that category and period. Anomalies are calculated using the Z-score. A Z-score is the number of" +
      " standard deviations a data point is from the mean. Anomalies are marked in red"


  currentTransactionInContextQuery!: TransactionInContextQuery;
  categoryMap!: CategoryMap;

  constructor(private appService: AppService, public dialog: MatDialog, private apiService: BudgetAssistantApiService) {
    this.appService.categoryMapObservable$.subscribe((categoryMap) => {
      if (categoryMap) {
        this.categoryMap = categoryMap;
      }
    });



  }

  initChartOptions(): any {
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
          mode: 'dataset', // or 'data' or 'label'
          // other options...
        }
      },
      indexAxis: 'y',
      tooltips: {
        mode: 'index',
        intersect: false
      },
      responsive: true,
      scales: {
        x: {
          stacked: true

        },
        y: {
          stacked: true


        }
      }
    };

  }



  doQuery() {
    if (!this.criteria) {
      throw new Error("Query parameters are not initialized!");
    }
    this.datatIsLoaded = false;
    let query: RevenueExpensesQuery = {
      accountNumber: this.criteria.bankAccount.accountNumber,
      grouping: this.criteria.grouping,
      transactionType: TransactionTypeEnum.BOTH,
      start: JSON.stringify(this.criteria.startDate),
      end: JSON.stringify(this.criteria.endDate),
      expensesRecurrence: RecurrenceType.BOTH,
      revenueRecurrence: RecurrenceType.BOTH

    };


    this.apiService.analysis.getRevenueAndExpensesPerPeriodAndCategoryApiAnalysisRevenueExpensesPerPeriodAndCategoryPost(query)
        .subscribe((res: RevenueAndExpensesPerPeriodAndCategory) => {
      // Transform the new response structure to chart data format
      this.expensesData = this.transformPeriodsToChartData(res.periods ?? [], res.allCategories ?? []);
      this.revenueData = this.transformPeriodsToChartData(res.periods ?? [], res.allCategories ?? []);

      // Transform periods to table data
      const tableData = this.transformPeriodsToTableData(res.periods ?? [], res.allCategories ?? []);

      // Build column names from periods + category column
      const columnNames = ['category', ...((res.periods ?? []).map(p => p.period))];
      this.displayedColumns = columnNames;
      this.displayedColumnsExceptFirst = this.displayedColumns.slice(1);
      this.firstColumn = this.displayedColumns[0];
      this.expensesDataSource = new MatTableDataSource<DistributionByCategoryForPeriodTableData>(tableData);
      this.expensesDataSourceAll = new MatTableDataSource<DistributionByCategoryForPeriodTableData>(tableData);
      this.revenueDataSource = new MatTableDataSource<DistributionByCategoryForPeriodTableData>(tableData);
      this.revenueDataSourceAll = new MatTableDataSource<DistributionByCategoryForPeriodTableData>(tableData);
      this.datatIsLoaded = true;
    })
  }

  transformPeriodsToChartData(periods: PeriodCategoryBreakdown[], allCategories: string[]): any {
    let labels: string[] = periods.map(p => p.period);
    let datasets: any[] = [];

    // Initialize datasets for each category
    allCategories.forEach(category => {
      datasets.push({
        label: category,
        data: []
      });
    });

    // Fill in the data for each period
    periods.forEach(periodData => {
      // Create a map of category -> amount for this period
      let categoryAmountMap: { [key: string]: number } = {};
      (periodData.categories ?? []).forEach((cat: CategoryAmount) => {
        categoryAmountMap[cat.categoryQualifiedName] = Math.abs(cat.amount ?? 0);
      });

      // Fill in the data for each dataset
      datasets.forEach(dataset => {
        dataset.data.push(categoryAmountMap[dataset.label] || 0);
        dataset.maxBarThickness = 50;
      });
    });

    return {
      labels: labels,
      datasets: datasets
    };
  }

  transformPeriodsToTableData(periods: PeriodCategoryBreakdown[], allCategories: string[]): DistributionByCategoryForPeriodTableData[] {
    // Transform periods data into table rows, one row per category
    return allCategories.map(category => {
      const row: DistributionByCategoryForPeriodTableData = { category };
      periods.forEach(period => {
        const categoryData = (period.categories ?? []).find((c: CategoryAmount) => c.categoryQualifiedName === category);
        row[period.period] = categoryData?.amount ?? 0;
      });
      return row;
    });
  }


  protected readonly TransactionType = TransactionTypeEnum;


  ngOnInit(): void {
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['criteria']?.currentValue) {
      this.doQuery();
    }

  }

  handleDataSelect($event: any) {
    console.log($event);
    let datasetIndex = $event.element.datasetIndex;
    if (this.criteria.transactionType === TransactionTypeEnum.EXPENSES) {
      let label = this.expensesData.labels[datasetIndex];
      let data = this.expensesData.datasets[datasetIndex].data;

    }

  }

  openContextMenu(period: string, category: number, event: MouseEvent) {
    //fixme: change data model so that we don't store category string but category object
    // Prevent the browser's default context menu from being opened
    event.preventDefault();

    this.currentTransactionInContextQuery = {
      period: period,
      categoryId: category,
      bankAccount: this.criteria.bankAccount.accountNumber,
      transactionType: this.criteria.transactionType as TransactionTypeEnum
    }


  }

  onShowTransactions() {
    //open TransactionsInContextDialogComponent and pass in currentTransactionInContextQuery
    const dialogRef = this.dialog.open(TransactionsInContextDialogComponent, {
      data: this.currentTransactionInContextQuery
    });





  }


  protected readonly TransactionTypeEnum = TransactionTypeEnum;
}
