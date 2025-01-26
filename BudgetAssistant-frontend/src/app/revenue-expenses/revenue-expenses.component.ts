import {Component, Input, OnChanges, OnInit, SimpleChanges, ViewChild} from '@angular/core';
import {MatPaginator} from "@angular/material/paginator";
import {MatSort} from "@angular/material/sort";
import {MatTable, MatTableDataSource} from "@angular/material/table";
import ChartDataLabels from 'chartjs-plugin-datalabels';
import {DistributionByTransactionTypeForPeriod, RevenueExpensesQuery, TransactionType} from '../model';
import {parse} from 'date-fns';
import {isNaN} from "lodash";
import {AppService} from "../app.service";
import {Criteria} from "../insights/insights.component";


@Component({
  selector: 'expenses-revenue',
  templateUrl: './revenue-expenses.component.html',
  styleUrls: ['./revenue-expenses.component.scss'],
  animations: []
})
export class ExpensesRevenueComponent  implements OnInit, OnChanges {


  //table stuff
  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;
  @ViewChild(MatTable) table!: MatTable<DistributionByTransactionTypeForPeriod>;
  dataSource!: MatTableDataSource<DistributionByTransactionTypeForPeriod>;
  displayedColumns = ["period", "revenue", "expenses", "balance"];

  tableIsHidden: boolean = true;
  barIsSelected: boolean = false;


  //chart stuff
  datatIsLoaded: Boolean = false;

  data: any;
  chartOptions: any;
  plugins: any[] = [ChartDataLabels];
  @Input() criteria!: Criteria;

  constructor(private appService: AppService) {


  }



  doQuery(): void {
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


    this.appService.getRevenueAndExpensesByYear(query).subscribe(result => {
      let content: DistributionByTransactionTypeForPeriod[] = result.content;
      this.dataSource = new MatTableDataSource(content);
      this.dataSource.sort = this.sort;
      this.dataSource.paginator = this.paginator;
      // this.table.dataSource = this.dataSource;
      this.handleChart(content);
      this.datatIsLoaded = true;
    });


  }

  handleChart(content: DistributionByTransactionTypeForPeriod[]) {

    let chartData: any[] = []


    this.datatIsLoaded = content.length > 0;
    content.forEach(item => {
      let entry = {
        "name": item.period.value, "series": [{
          "name": "inkomsten", "value": item.revenue, "extra": item

        }, {
          "name": "uitgaven", "value": Math.abs(item.expenses), "extra": item

        }]

      }

      chartData.push(entry)
    })

    if (chartData.length > 0) {
      this.data = this.transformChartDataToPrimeNgFormat(chartData);
      this.chartOptions = this.initChartOptions();
    }


  }

  transformChartDataToPrimeNgFormat(chartData: any[]):
      any {
    let transformedData: any = {
      labels: [],
      datasets: [
        {
          type: 'bar',
          label: 'Inkomsten',
          backgroundColor: '#66BB6A',
          data: []
        },
        {
          type: 'bar',
          label: 'Uitgaven',
          backgroundColor: '#EF5350',
          data: []
        }
      ]
    };

    chartData.forEach(item => {
      transformedData.labels.push(item.name);
      item.series.forEach((seriesItem: any) => {
        if (seriesItem.name === 'inkomsten') {
          transformedData.datasets[0].data.push(seriesItem.value);
        }
        else if (seriesItem.name === 'uitgaven') {
          transformedData.datasets[1].data.push(seriesItem.value);
        }
      });
    });

    return transformedData;
  }


  initChartOptions(): any {
    return {
      plugins: {
        datalabels: {
          display: true,
          align: 'end',
          anchor: 'end',
          formatter: function (value:any, context:any) { return Math.round(value) || null;  }
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
          stacked: false

        },
        y: {
          stacked: false


        }
      }
    };

  }


  toggleTable() {
    this.tableIsHidden = !this.tableIsHidden;
  }


  getToggleTableMessage() {

    if (!this.tableIsHidden) {
      return "verberg tabel";
    }

    return "toon tabel"

  }

  /*handleBarIsSelected($event: any): void {
    //check if event is an object
    if (typeof $event !== 'object'
    ) {
      return;
    }

    let period: Period = $event.extra.period;
    let start = this.stringToDate(period.start);
    let end = this.stringToDate(period.end);


    let query: RevenueExpensesQuery = {
      accountNumber: this.criteria.bankAccount.accountNumber,
      grouping: this.criteria.grouping,
      transactionType: TransactionType.BOTH,
      start: start,
      end: end,
      expensesRecurrence: 'both',
      revenueRecurrence: 'both'
    }

    this.appService.setCategoryQueryForSelectedPeriod$(query);
    this.barIsSelected = true;


  }*/

  private stringToDate(string: string): Date {

    const dateObject = parse(string, 'yyyy-MM-dd', new Date());

    if (!isNaN(dateObject.getTime())) {
      return dateObject;
    }
    else {
      throw new Error("Invalid error")
    }

  }

  ngOnInit(): void {

  }

  ngOnChanges(changes: SimpleChanges): void {

    if (changes['criteria']?.currentValue) {
      this.doQuery();
    }

  }

}

