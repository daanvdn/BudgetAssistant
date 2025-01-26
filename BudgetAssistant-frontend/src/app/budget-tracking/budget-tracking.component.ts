import {Component, Input, OnChanges, OnInit, SimpleChanges} from '@angular/core';

import {AppService} from '../app.service';
import {RevenueExpensesQuery, TransactionType} from '../model';
import {Criteria} from "../insights/insights.component";
// @ts-ignore
import autocolors from 'chartjs-plugin-autocolors';
import {MatTableDataSource} from "@angular/material/table";
import {TreeNode} from "primeng/api";


@Component({
    selector: 'budget-tracking',
    templateUrl: './budget-tracking.component.html',
    styleUrls: ['./budget-tracking.component.scss']
})
export class BudgetTrackingComponent implements OnInit, OnChanges {

    @Input() criteria!: Criteria
    datatIsLoaded: Boolean = false;
    treeNodes!: TreeNode[];
    columns!: string[];

    // Add these properties to your component
    dataSource!: MatTableDataSource<any>;
    displayedColumns!: string[];


    constructor(private appService: AppService) {


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


        this.appService.trackBudget(query).subscribe(res => {
            /*this.treeNodes= res.data;
            this.columns = res.columns;
             this.datatIsLoaded = true;*/
            this.dataSource = new MatTableDataSource(res.data);
            this.displayedColumns = res.columns;
            this.datatIsLoaded = true;
        })
    }

    ngOnInit(): void {
    }

    ngOnChanges(changes: SimpleChanges): void {
        if (changes['criteria']?.currentValue) {
            this.doQuery();
        }

    }

    protected readonly TransactionType = TransactionType;



    getCellValue(element: any, column: string) {
        //check if element has the column

        let value = element.data[column];
        if (value !== null && value !== undefined) {
            if (typeof value === 'number') {
                return value.toFixed(0);
            }
            return value

        }
        return "N/A";
    }
}




