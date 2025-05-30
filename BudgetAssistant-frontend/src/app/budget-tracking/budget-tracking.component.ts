import {Component, Input, OnChanges, OnInit, SimpleChanges} from '@angular/core';

import {AppService} from '../app.service';
import {Criteria} from "../model/criteria.model";
// @ts-ignore
import autocolors from 'chartjs-plugin-autocolors';
import {
    MatCell,
    MatCellDef,
    MatColumnDef,
    MatHeaderCell,
    MatHeaderCellDef,
    MatHeaderRow,
    MatHeaderRowDef,
    MatRow,
    MatRowDef,
    MatTable,
    MatTableDataSource
} from "@angular/material/table";
import {TreeNode} from "primeng/api";
import {
    ApiBudgetAssistantBackendClientService,
    BudgetTrackerResult,
    ExpensesRecurrenceEnum,
    RevenueExpensesQuery,
    TransactionTypeEnum
} from "@daanvdn/budget-assistant-client";
import {RevenueRecurrenceEnum} from "@daanvdn/budget-assistant-client";
import {catchError, throwError} from "rxjs";
import {NgFor, NgIf} from '@angular/common';

@Component({
    selector: 'budget-tracking',
    templateUrl: './budget-tracking.component.html',
    styleUrls: ['./budget-tracking.component.scss'],
    standalone: true,
    imports: [NgIf, MatTable, NgFor, MatColumnDef, MatHeaderCellDef, MatHeaderCell, MatCellDef, MatCell, MatHeaderRowDef, MatHeaderRow, MatRowDef, MatRow]
})
export class BudgetTrackingComponent implements OnInit, OnChanges {

    @Input() criteria!: Criteria
    datatIsLoaded: Boolean = false;
    treeNodes!: TreeNode[];
    columns!: string[];

    // Add these properties to your component
    dataSource!: MatTableDataSource<any>;
    displayedColumns!: string[];


    constructor(private appService: AppService, private apiBudgetAssistantBackendClientService: ApiBudgetAssistantBackendClientService) {


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
            expensesRecurrence: ExpensesRecurrenceEnum.BOTH,
            revenueRecurrence: RevenueRecurrenceEnum.BOTH

        };
        this.apiBudgetAssistantBackendClientService.apiTrackBudgetCreate(query).pipe(
            catchError(error => {
                console.error('Error occurred:', error);
                return throwError(error);
            })
        ).subscribe((res: BudgetTrackerResult) => {
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

    protected readonly TransactionType = TransactionTypeEnum;



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
