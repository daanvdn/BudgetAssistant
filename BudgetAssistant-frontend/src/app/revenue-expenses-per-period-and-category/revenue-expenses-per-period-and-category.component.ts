import {Component, Input, OnChanges, OnInit, SimpleChanges, ViewChild} from '@angular/core';
import ChartDataLabels from 'chartjs-plugin-datalabels';

import {AppService} from '../app.service';
import {
  DistributionByCategoryForPeriodChartData,
  DistributionByCategoryForPeriodTableData,
  Period,
  RevenueExpensesQuery, TransactionsInContextQuery,
  TransactionType
} from '../model';
import {Criteria} from "../insights/insights.component";
// @ts-ignore
import autocolors from 'chartjs-plugin-autocolors';
import {MatTable, MatTableDataSource} from "@angular/material/table";
import {CategoryAndPeriod, ContextMenuService} from "./context-menu.service";
import {MatDialog} from "@angular/material/dialog";
import {TransactionsInContextDialogComponent} from "../transaction-dialog/transactions-in-context-dialog.component";


@Component({
  selector: 'revenue-expenses-per-period-and-category',
  templateUrl: './revenue-expenses-per-period-and-category.component.html',
  styleUrls: ['./revenue-expenses-per-period-and-category.component.scss']
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


  currentTransactionInContextQuery!: TransactionsInContextQuery;

  constructor(private appService: AppService, public dialog: MatDialog) {



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
      transactionType: TransactionType.BOTH,
      start: this.criteria.startDate,
      end: this.criteria.endDate,
      expensesRecurrence: 'both',
      revenueRecurrence: 'both'

    };


    this.appService.getRevenueExpensesPerPeriodAndCategory(query).subscribe(res => {
      this.expensesData = this.transformChartDataToPrimeNgFormat(res.chartDataExpenses);
      this.revenueData = this.transformChartDataToPrimeNgFormat(res.chartDataRevenue);
      let tableDataRevenue: DistributionByCategoryForPeriodTableData[] = res.tableDataRevenue;
      let tableDataExpenses: DistributionByCategoryForPeriodTableData[] = res.tableDataExpenses;
      this.displayedColumns = res.tableColumnNames.filter(column => column !== 'categoryId');
      this.displayedColumnsExceptFirst = this.displayedColumns.slice(1);
      this.firstColumn = this.displayedColumns[0];
      this.expensesDataSource = new MatTableDataSource<DistributionByCategoryForPeriodTableData>(tableDataExpenses);
      this.expensesDataSourceAll = new MatTableDataSource<DistributionByCategoryForPeriodTableData>(tableDataExpenses);
      this.revenueDataSource = new MatTableDataSource<DistributionByCategoryForPeriodTableData>(tableDataRevenue);
      this.revenueDataSourceAll = new MatTableDataSource<DistributionByCategoryForPeriodTableData>(tableDataRevenue);
      this.datatIsLoaded = true;
    })
  }


  transformChartDataToPrimeNgFormat(chartData: DistributionByCategoryForPeriodChartData[]): any {
    let labels: string[] = [];
    let datasets: any[] = [];

    // First, we need to get all unique categories across all periods
    let allCategories: string[] = [];
    chartData.forEach(data => {
      data.entries.forEach(entry => {
        if (!allCategories.includes(entry.category)) {
          allCategories.push(entry.category);
        }
      });
    });

    // Initialize datasets for each category
    allCategories.forEach(category => {
      datasets.push({
        label: category,
        //backgroundColor: '#' + (Math.random() * 0xFFFFFF << 0).toString(16), // generate random color
        data: []
      });
    });

    // Fill in the data for each period
    chartData.forEach(data => {
      labels.push((data.period as Period).value);

      // Initialize a map to store the amount for each category in this period
      let categoryAmountMap: { [key: string]: number } = {};
      data.entries.forEach(entry => {
        categoryAmountMap[entry.category] = Math.abs(entry.amount);
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


  protected readonly TransactionType = TransactionType;


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
    if (this.criteria.transactionType === TransactionType.EXPENSES) {
      let label = this.expensesData.labels[datasetIndex];
      let data = this.expensesData.datasets[datasetIndex].data;

    }

  }

  openContextMenu(period: string, category: string, event: MouseEvent) {
    // Prevent the browser's default context menu from being opened
    event.preventDefault();

    this.currentTransactionInContextQuery = {
      period: period,
      category: category,
      bankAccount: this.criteria.bankAccount.accountNumber,
      transactionType : this.criteria.transactionType as TransactionType
    }


  }

  onShowTransactions() {
    //open TransactionsInContextDialogComponent and pass in currentTransactionInContextQuery
    const dialogRef = this.dialog.open(TransactionsInContextDialogComponent, {
      data: this.currentTransactionInContextQuery
    });





  }


}




