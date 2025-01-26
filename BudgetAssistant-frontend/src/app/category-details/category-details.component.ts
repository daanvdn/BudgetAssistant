import {Component, Input, OnChanges, OnInit, SimpleChanges} from '@angular/core';
import {BankAccount, Dataset, RevenueExpensesQuery, TransactionType} from "../model";
import {AppService} from "../app.service";
import ChartDataLabels from "chartjs-plugin-datalabels";
import {Observable} from "rxjs";
import {MatSelectionListChange} from "@angular/material/list";
// @ts-ignore
import autocolors from 'chartjs-plugin-autocolors';


import {Criteria} from "../insights/insights.component";


interface Category {
    name: string;
    transactionType: TransactionType;

}
@Component({
    selector: 'category-details',
    templateUrl: './category-details.component.html',
    styleUrls: ['./category-details.component.scss']
})
export class CategoryDetailsComponent implements OnInit, OnChanges {

    /* executedInitialQuery: boolean = false;
     criteriaChangeCount: number = 0;
     criteria: Criteria | undefined;*/


    selectedCategory: Category | undefined;
    plugins: any[] = [ChartDataLabels, autocolors];
    expensesCategories!: Category[];
    revenueCategories!: Category[];
    chartData: any;

    datatIsLoaded: Boolean = false;
    chartOptions: any = this.initChartOptions();
    @Input() criteria!: Criteria;

    constructor(private appService: AppService) {

        this.appService.selectedBankAccountObservable$.subscribe(bankAccount => {
            if (bankAccount) {
                this.initCategoryLists(bankAccount);
            }

        });

    }


    private initCategoryLists(bankAccount: BankAccount) {
        this.getCategories(bankAccount, TransactionType.EXPENSES).subscribe((data) => {
            this.expensesCategories = data.map((category: string) => {
                return {name: category, transactionType: TransactionType.EXPENSES};
            });
        });
        this.getCategories(bankAccount, TransactionType.REVENUE).subscribe((data) => {
            this.revenueCategories = data.map((category: string) => {
                return {name: category, transactionType: TransactionType.REVENUE};
            });
        });
    }


    ngOnInit(): void {

    }



    initChartOptions(): any {
        return {
            plugins: {
                datalabels: {
                    display: true,
                    align: 'end',
                    anchor: 'end',
                    formatter: function (value: any, context: any) {
                        return Math.round(value) || null;
                    }

                },
                autocolors: {
                    enabled: true,
                    mode: 'dataset', // or 'data' or 'label'
                    // other options...
                }
            },
            indexAxis: 'x',
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


    doQuery(): void {

        this.datatIsLoaded = false;

        if (!this.criteria || !this.selectedCategory) {
            return;
        }
        if(this.selectedCategory.transactionType !== this.criteria.transactionType) {
            return;
        }

        let query: RevenueExpensesQuery = {
            accountNumber: this.criteria.bankAccount.accountNumber,
            grouping: this.criteria.grouping,
            transactionType: this.criteria.transactionType,
            start: this.criteria.startDate,
            end: this.criteria.endDate,
            expensesRecurrence: 'both',
            revenueRecurrence: 'both'

        };


        this.datatIsLoaded = false;
        this.appService.getCategoryDetailsForPeriod(query, this.selectedCategory.name).subscribe((data) => {
            data.datasets = data.datasets.map((dataset: Dataset) => {
                dataset.maxBarThickness = 50
                return dataset;
            });
            this.chartData = data;
            this.datatIsLoaded = true;
        });

    }


    private getCategories(bankAccount: BankAccount, transactionType: TransactionType):
        Observable<string[]> {
        if (transactionType === TransactionType.BOTH) {
            throw new Error("TransactionType.BOTH is not supported");
        }

        return this.appService.getCategoriesForAccountAndTransactionType(bankAccount.accountNumber, transactionType);

    }


    onCategorySelectionChange($event: MatSelectionListChange) {
        let options = $event.options;
        if (options) {
            this.selectedCategory = options[0].value as Category;
            this.doQuery();
        }

    }

    protected readonly TransactionType = TransactionType;

    ngOnChanges(changes: SimpleChanges): void {
        let criteriaChange = changes['criteria'];
        if (criteriaChange && criteriaChange.currentValue) {
            let previousCriteria = criteriaChange.previousValue;
            if (previousCriteria && this.criteria && previousCriteria.transactionType !== this.criteria.transactionType) {
                this.selectedCategory = undefined;
            }
            this.doQuery();
         }

    }
}
