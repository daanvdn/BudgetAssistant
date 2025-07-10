import {Component, Input, OnChanges, OnInit, SimpleChanges} from '@angular/core';
import {Dataset} from "../model";
import {AppService} from "../app.service";
import ChartDataLabels from "chartjs-plugin-datalabels";
import {Observable} from "rxjs";
import {MatListOption, MatSelectionList, MatSelectionListChange} from "@angular/material/list";
// @ts-ignore
import autocolors from 'chartjs-plugin-autocolors';
import {
    BankAccount,
    ExpensesRecurrenceEnum,
    RevenueExpensesQuery,
    RevenueRecurrenceEnum,
    TransactionTypeEnum
} from "@daanvdn/budget-assistant-client";

import {Criteria} from "../model/criteria.model";
import {NgFor, NgIf} from '@angular/common';
import {ChartModule} from 'primeng/chart';
import {
    RevenueExpensesQueryWithCategory
} from "@daanvdn/budget-assistant-client/dist/model/revenue-expenses-query-with-category";
import {effect} from "@angular/core";

interface Category {
    name: string;
    transactionType: TransactionTypeEnum;

}
@Component({
    selector: 'category-details',
    templateUrl: './category-details.component.html',
    styleUrls: ['./category-details.component.scss'],
    standalone: true,
    imports: [NgIf, MatSelectionList, NgFor, MatListOption, ChartModule]
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
// Usage in components
        effect(() => {
            const selected = this.appService.selectedBankAccount();
            if (selected) {
                this.initCategoryLists(selected);
            }
        });

    }


    private initCategoryLists(bankAccount: BankAccount) {
        this.getCategories(bankAccount, TransactionTypeEnum.EXPENSES).subscribe((data) => {
            this.expensesCategories = data.map((category: string) => {
                return {name: category, transactionType: TransactionTypeEnum.EXPENSES};
            });
        });
        this.getCategories(bankAccount, TransactionTypeEnum.REVENUE).subscribe((data) => {
            this.revenueCategories = data.map((category: string) => {
                return {name: category, transactionType: TransactionTypeEnum.REVENUE};
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

        let query: RevenueExpensesQueryWithCategory = {
            accountNumber: this.criteria.bankAccount.accountNumber,
            grouping: this.criteria.grouping,
            transactionType: this.criteria.transactionType,
            start: JSON.stringify(this.criteria.startDate),
            end: JSON.stringify(this.criteria.endDate),
            expensesRecurrence: ExpensesRecurrenceEnum.BOTH,
            revenueRecurrence: RevenueRecurrenceEnum.BOTH,
            category: this.selectedCategory.name

        };


        this.datatIsLoaded = false;
        this.appService.getCategoryDetailsForPeriod(query).subscribe((data) => {
            data.datasets = data.datasets.map((dataset: Dataset) => {
                dataset.maxBarThickness = 50
                return dataset;
            });
            this.chartData = data;
            this.datatIsLoaded = true;
        });

    }


    private getCategories(bankAccount: BankAccount, transactionType: TransactionTypeEnum):
        Observable<string[]> {
        if (transactionType === TransactionTypeEnum.BOTH) {
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

    protected readonly TransactionType = TransactionTypeEnum;

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
