import {AfterViewInit, Component, Inject, OnInit} from '@angular/core';
import {PaginationDataSource} from "ngx-pagination-data-source";
import {AppService} from "../app.service";
import {MAT_LEGACY_DIALOG_DATA as MAT_DIALOG_DATA, MatLegacyDialogRef as MatDialogRef} from "@angular/material/legacy-dialog";
import {Transaction, TransactionQuery, TransactionInContextQuery} from "@daanvdn/budget-assistant-client";
import {AmountType, inferAmountType} from "../model";

@Component({
    selector: 'transactions-in-context-dialog',
    templateUrl: './transactions-in-context-dialog.component.html',
    styleUrls: ['./transactions-in-context-dialog.component.scss']
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

    constructor(private appService: AppService, public dialogRef: MatDialogRef<TransactionsInContextDialogComponent>,
                @Inject(MAT_DIALOG_DATA) public query: TransactionInContextQuery) {
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
        transaction.category = {qualifiedName:selectedCategoryQualifiedNameStr};
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
