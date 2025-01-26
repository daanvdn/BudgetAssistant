import {Component, OnInit} from '@angular/core';
import {AppService} from "../app.service";
import {LegendPosition} from "@swimlane/ngx-charts";
import {DistributionByCategoryForPeriodChartData, Period} from "../model";



@Component({
  selector: 'analysis-for-period-by-category',
  templateUrl: './analysis-for-period-by-category.component.html',
  styleUrls: ['./analysis-for-period-by-category.component.scss'],

})
export class AnalysisForPeriodByCategoryComponent implements OnInit {

  //data
  single: any[] = [];
  public incomeDataPieChart: PieChartData[] = [];
  public expensesDataPieChart: PieChartData[] = [];

  //
  isLoaded: boolean = false;

  // options
  view: [number, number] = [700, 400];
  gradient: boolean = true;
  showLegend: boolean = false;
  showLabels: boolean = true;
  isDoughnut: boolean = false;
  legendPosition: LegendPosition = LegendPosition.Below;

  customColors: any[] = [];


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
        for (const label of labelColors.keys()) {
          let color = labelColors.get(label);
          this.customColors.push({"name": label,"value": color})
        }


      })
    })
  }




}

export class PieChartData {
  nameValuePairs: any[];
  period: Period;


  constructor(nameValuePairs: any[], period: Period) {
    this.nameValuePairs = nameValuePairs;
    this.period = period;
  }

  static fromDistributionByCategoryForPeriodChartData(obj: DistributionByCategoryForPeriodChartData, labelColors: Map<string, string>): PieChartData {
    let arr: any[] = [];
    obj.entries.forEach((categoryAndAmount => {
      let result = {
        "name": categoryAndAmount.category,
        "value": Math.abs(categoryAndAmount.amount)
      };
      arr.push(result);
      getColorForLabel(result.name, labelColors)


    }))
    return new PieChartData(arr, obj.period as Period);

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




