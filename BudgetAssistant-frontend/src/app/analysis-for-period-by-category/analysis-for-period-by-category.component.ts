import {Component, OnInit} from '@angular/core';
import {AppService} from "../app.service";
import {BaseChartDirective} from 'ng2-charts';
import {ChartData, ChartOptions} from 'chart.js';
import {DistributionByCategoryForPeriodChartData, Period} from "../model";
import { NgIf, NgFor } from '@angular/common';
import { MatCard, MatCardHeader, MatCardContent } from '@angular/material/card';



@Component({
    selector: 'analysis-for-period-by-category',
    templateUrl: './analysis-for-period-by-category.component.html',
    styleUrls: ['./analysis-for-period-by-category.component.scss'],
    standalone: true,
    imports: [
        NgIf,
        NgFor,
        MatCard,
        MatCardHeader,
        MatCardContent,
        BaseChartDirective,
    ],
})
export class AnalysisForPeriodByCategoryComponent implements OnInit {

  //data
  single: any[] = [];
  public incomeDataPieChart: PieChartData[] = [];
  public expensesDataPieChart: PieChartData[] = [];

  //
  isLoaded: boolean = false;

  // Chart.js options
  pieChartOptions: ChartOptions<'pie'> = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        display: true,
        position: 'bottom'
      }
    }
  };


  constructor(public appService: AppService) {
    this.isLoaded = false;
  }


  ngOnInit(): void {

    let labelColors: Map<string, string> = new Map<string, string>();
    this.appService.categoryQueryForSelectedPeriodObservable$.subscribe(query => {
      if(!query){
        return;
      }
      this.appService.getRevenueExpensesPerPeriodAndCategoryShow1MonthBeforeAndAfter(query).subscribe(result => {
        this.expensesDataPieChart = [];
        for (const expense of result.chartDataExpenses) {
          this.expensesDataPieChart.push(PieChartData.fromDistributionByCategoryForPeriodChartData(expense, labelColors));
        }

        this.incomeDataPieChart = [];
        for (const income of result.chartDataRevenue) {
          this.incomeDataPieChart.push(PieChartData.fromDistributionByCategoryForPeriodChartData(income, labelColors))
        }

        this.isLoaded = true;


      })
    })
  }




}

export class PieChartData {
  chartData: ChartData<'pie', number[], string>;
  period: Period;


  constructor(chartData: ChartData<'pie', number[], string>, period: Period) {
    this.chartData = chartData;
    this.period = period;
  }

  static fromDistributionByCategoryForPeriodChartData(obj: DistributionByCategoryForPeriodChartData, labelColors: Map<string, string>): PieChartData {
    const labels: string[] = [];
    const data: number[] = [];
    const backgroundColors: string[] = [];

    obj.entries.forEach((categoryAndAmount => {
      labels.push(categoryAndAmount.category);
      data.push(Math.abs(categoryAndAmount.amount));
      backgroundColors.push(getColorForLabel(categoryAndAmount.category, labelColors));
    }));

    const chartData: ChartData<'pie', number[], string> = {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: backgroundColors
      }]
    };

    return new PieChartData(chartData, obj.period as Period);

  }
}

function getRandomColor() {
  return '#' + Math.floor(Math.random()*16777215).toString(16);
}


function getColorForLabel(label: string, labelColors: Map<string, string>): string {

  if (!labelColors.get(label)) {

    labelColors.set(label, getRandomColor());
  }

  return labelColors.get(label) as string;
}