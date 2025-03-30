import {AfterViewInit, Component, Inject, OnInit} from '@angular/core';
import {PaginationDataSource} from "@daanvdn/ngx-pagination-data-source";
import {AppService} from "../app.service";
import {
    MAT_DIALOG_DATA,
    MatDialogActions,
    MatDialogContent,
    MatDialogRef,
    MatDialogTitle
} from "@angular/material/dialog";
import {Transaction, TransactionInContextQuery} from "@daanvdn/budget-assistant-client";
import {AmountType, CategoryMap, inferAmountType} from "../model";
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

@Component({
    selector: 'transactions-in-context-dialog',
    templateUrl: './transactions-in-context-dialog.component.html',
    styleUrls: ['./transactions-in-context-dialog.component.scss'],
    standalone: true,
    imports: [MatDialogTitle, MatDialogContent, MatTable, MatSort, MatColumnDef, MatHeaderCellDef, MatHeaderCell, MatSortHeader, MatCellDef, MatCell, NgIf, CategoryTreeDropdownComponent, MatHeaderRowDef, MatHeaderRow, MatRowDef, MatRow, MatPaginator, MatDialogActions, MatButton, AsyncPipe, TitleCasePipe, DatePipe]
})
export class TransactionsInContextDialogComponent implements OnInit, AfterViewInit {
    dataSource!: PaginationDataSource<Transaction, TransactionInContextQuery>;
    displayedColumns = [
        "bookingDate",
        "counterparty",
        "transaction",
        "amount",
        "transactionType"
    ];
    private currentSort?: any;
    private categoryMap?: CategoryMap;

    constructor(private appService: AppService, public dialogRef: MatDialogRef<TransactionsInContextDialogComponent>,
                @Inject(MAT_DIALOG_DATA) public query: TransactionInContextQuery) {
        this.appService.categoryMapObservable$.subscribe(categoryMap => {
            this.categoryMap = categoryMap;
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

        this.dataSource = new PaginationDataSource<Transaction, TransactionInContextQuery>(
            (request, query) => {
                request.size = 50;
                return this.appService.pageTransactionsInContext(request, query);
            },
            newSort, transactionQuery
        );


    }

    setCategory(transaction: Transaction, selectedCategoryQualifiedNameStr: string) {
        let simpleCategory = this.categoryMap?.getSimpleCategory(selectedCategoryQualifiedNameStr);
        if (! simpleCategory){
            throw new Error("No category found for " + selectedCategoryQualifiedNameStr);
        }
        transaction.category = simpleCategory;
        this.saveTransaction(transaction);
    }

    saveTransaction(transaction: Transaction) {
        this.appService.saveTransaction(transaction)
    }

    amountType(transaction: Transaction): AmountType {
        if (transaction.amount === undefined || transaction.amount === null) {
            return AmountType.BOTH;
        }
        return inferAmountType(transaction.amount)


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
