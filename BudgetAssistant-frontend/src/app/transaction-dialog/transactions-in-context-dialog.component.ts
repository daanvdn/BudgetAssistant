import {AfterViewInit, Component, Inject, OnInit} from '@angular/core';
import {PaginationDataSource} from "ngx-pagination-data-source";
import {AppService} from "../app.service";
import {
    MAT_DIALOG_DATA,
    MatDialogActions,
    MatDialogContent,
    MatDialogRef,
    MatDialogTitle
} from "@angular/material/dialog";
import {CategoryIndex, TransactionRead, TransactionInContextQuery} from "@daanvdn/budget-assistant-client";
import {AmountType, inferAmountType} from "../model";
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
    MatTable
} from '@angular/material/table';
import {MatSort, MatSortHeader} from '@angular/material/sort';
import {AsyncPipe, DatePipe, NgIf, TitleCasePipe} from '@angular/common';
import {CategoryTreeDropdownComponent} from '../category-tree-dropdown/category-tree-dropdown.component';
import {MatPaginator} from '@angular/material/paginator';
import {MatButton} from '@angular/material/button';
import {DateUtilsService} from '../shared/date-utils.service';

@Component({
    selector: 'transactions-in-context-dialog',
    templateUrl: './transactions-in-context-dialog.component.html',
    styleUrls: ['./transactions-in-context-dialog.component.scss'],
    standalone: true,
    imports: [MatDialogTitle, MatDialogContent, MatTable, MatSort, MatColumnDef, MatHeaderCellDef, MatHeaderCell, MatSortHeader, MatCellDef, MatCell, NgIf, CategoryTreeDropdownComponent, MatHeaderRowDef, MatHeaderRow, MatRowDef, MatRow, MatPaginator, MatDialogActions, MatButton, AsyncPipe, TitleCasePipe, DatePipe]
})
export class TransactionsInContextDialogComponent implements OnInit, AfterViewInit {
    dataSource!: PaginationDataSource<TransactionRead, TransactionInContextQuery>;
    displayedColumns = [
        "bookingDate",
        "counterparty",
        "transaction",
        "amount",
        "transactionType"
    ];
    private currentSort?: any;
    private categoryIndex?: CategoryIndex;

    constructor(private appService: AppService, public dialogRef: MatDialogRef<TransactionsInContextDialogComponent>,
                @Inject(MAT_DIALOG_DATA) public query: TransactionInContextQuery, private dateUtils: DateUtilsService) {
        this.appService.categoryIndexObservable$.subscribe(categoryIndex => {
            this.categoryIndex = categoryIndex;
        });
    }

    ngOnInit(): void {
        this.doQuery(this.query);
    }

    sortBy(event: any) {
        let key = event.active;
        let direction = event.direction;
        this.currentSort = {
            property: key,
            order: direction || "ASC"

        };
        this.dataSource.sortBy(this.currentSort);
    }

    doQuery(transactionQuery: TransactionInContextQuery | undefined): void {
        if (transactionQuery === undefined) {
            return;
        }

        let newSort;
        if (this.currentSort !== undefined) {
            newSort = this.currentSort;
        }
        else {

            newSort = {property: 'bookingDate', order: 'desc'}
            this.currentSort = newSort;
        }

        this.dataSource = new PaginationDataSource<TransactionRead, TransactionInContextQuery>(
            (request:any, query:any) => {
                request.size = 50;
                return this.appService.pageTransactionsInContext(request, query);
            },
            newSort, transactionQuery
        );


    }

    setCategory(transaction: TransactionRead, selectedCategoryQualifiedNameStr: string) {
        let category = this.categoryIndex?.qualifiedNameToCategoryIndex[selectedCategoryQualifiedNameStr];
        if (!category){
            throw new Error("No category found for " + selectedCategoryQualifiedNameStr);
        }
        this.appService.saveTransactionWithCategoryId(transaction, category.id);
    }

    saveTransaction(transaction: TransactionRead) {
        this.appService.saveTransaction(transaction)
    }

    amountType(transaction: TransactionRead): AmountType {
        if (transaction.amount === undefined || transaction.amount === null) {
            return AmountType.BOTH;
        }
        return inferAmountType(transaction.amount)
    }

    parseDate(dateStr: string | undefined | null): Date | null {
        return this.dateUtils.parseDate(dateStr);
    }
    onCloseClick(): void {
        this.dialogRef.close();
    }

    ngAfterViewInit(): void {
        /**
         * logic to make dialog scroll to top
         */
        let element : Element |null = document.querySelector("#first");
        if(element !== null){
            element.scrollIntoView(true);
        }
    }


}
