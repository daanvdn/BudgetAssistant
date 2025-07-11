import {Component, effect, ElementRef, OnInit, ViewChild} from '@angular/core';
import {MatPaginator} from "@angular/material/paginator";
import {MatSort} from "@angular/material/sort";
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
} from "@angular/material/table";
import {PaginationDataSource, SimpleDataSource} from "ngx-pagination-data-source";
import {AppService} from "../app.service";
import {BehaviorSubject, map, Observable} from "rxjs";
import {MatButtonToggle, MatButtonToggleChange, MatButtonToggleGroup} from "@angular/material/button-toggle";
import {BankAccount, SimpleCategory, Transaction, TransactionTypeEnum} from "@daanvdn/budget-assistant-client";
import {AmountType, CategoryMap, inferAmountType} from "../model";
import {MatToolbar} from '@angular/material/toolbar';
import {BankAccountSelectionComponent} from '../bank-account-selection/bank-account-selection.component';
import {AsyncPipe, NgIf} from '@angular/common';
import {CategoryTreeDropdownComponent} from '../category-tree-dropdown/category-tree-dropdown.component';


interface GroupBy {
    counterparty: string;
    isGroupBy: boolean;
    transactions: Transaction[];
    isExpense: boolean;
}

class GroupByCounterpartyDataSource implements SimpleDataSource<Transaction | GroupBy> {


    constructor(public backingPaginationDataSource: PaginationDataSource<Transaction, BankAccount>,
                private isExpense: boolean) {
    }

    connect(): Observable<Array<Transaction | GroupBy>> {
        return this.backingPaginationDataSource.connect().pipe(map(data => {

            let mapByCounterpartyName = new Map<string, Transaction[]>();

            for (const transaction of data) {
                let name = transaction.counterparty.name;
                if (!name) {
                    name = "";
                }
                let transactionsForCounterparty = mapByCounterpartyName.has(name) ? mapByCounterpartyName.get(
                    name) : [];
                transactionsForCounterparty?.push(transaction);
                mapByCounterpartyName.set(name, transactionsForCounterparty as Transaction[]);
            }
            let sortedKeys = Array.from(mapByCounterpartyName.keys()).sort();
            let result = new Array<Transaction | GroupBy>();
            for (const aKey of sortedKeys) {
                let transactionsForKey = mapByCounterpartyName.get(aKey) as Transaction[];
                let groupBy: GroupBy = {
                    counterparty: aKey, isGroupBy: true, transactions: transactionsForKey, isExpense: this.isExpense
                };
                result.push(groupBy)
                result.push(...transactionsForKey)

            }

            return result;
        }));
    }

    disconnect(): void {
        this.backingPaginationDataSource.disconnect();
    }


    fetch(page: number, pageSize?: number): void {
        this.backingPaginationDataSource.fetch(page, pageSize);
    }


}

@Component({
    selector: 'app-manual-categorization-view',
    templateUrl: './manual-categorization-view.component.html',
    styleUrls: ['./manual-categorization-view.component.scss'],
    standalone: true,
    imports: [MatToolbar, BankAccountSelectionComponent, MatButtonToggleGroup, MatButtonToggle, NgIf, MatPaginator, MatTable, MatColumnDef, MatHeaderCellDef, MatHeaderCell, MatCellDef, MatCell, CategoryTreeDropdownComponent, MatHeaderRowDef, MatHeaderRow, MatRowDef, MatRow, AsyncPipe]
})
export class ManualCategorizationViewComponent implements OnInit {

    @ViewChild(MatPaginator, {static: false}) paginator!: MatPaginator;
    @ViewChild(MatSort, {static: false}) sort!: MatSort;
    @ViewChild(MatTable) table!: MatTable<Transaction>;
    @ViewChild('table', {read: ElementRef, static: false}) tableElement!: ElementRef;


    dataSource!: GroupByCounterpartyDataSource;
    categoryMap!: CategoryMap;

    private bankAccount!: BankAccount;
    displayedColumns = [
        "transaction",
        "amount",
        "category"
    ];
    private activeView: BehaviorSubject<TransactionTypeEnum> = new BehaviorSubject<TransactionTypeEnum>(
        TransactionTypeEnum.EXPENSES);
    private activeViewObservable = this.activeView.asObservable();

    constructor(private appService: AppService) {

        effect(() => {
            const selectedBankAccount = this.appService.selectedBankAccount();
            if (selectedBankAccount) {
                this.bankAccount = selectedBankAccount;
                this.dataSource = this.initDataSource(selectedBankAccount, this.activeView.getValue());
            }
        });

        effect(() => {

            const categoryMap = this.appService.categoryMap();
            if (categoryMap) {
                this.categoryMap = categoryMap;
            }
        });


        this.activeViewObservable.subscribe(activeView => {
            this.dataSource = this.initDataSource(this.bankAccount, activeView);
        })

    }

    ngOnInit(): void {
    }

    private initDataSource(account: BankAccount, transactionType: TransactionTypeEnum): GroupByCounterpartyDataSource {
        if (transactionType == TransactionTypeEnum.BOTH) {
            throw new Error("TransactionType.BOTH not supported")
        }

        let isExpense = transactionType === TransactionTypeEnum.EXPENSES;

        let paginationDataSource = new PaginationDataSource<Transaction, BankAccount>(
            (request: any, query: any) => {
                request.size = 50;
                return this.appService.pageTransactionsToManuallyReview(request, transactionType);
            },
            {property: 'counterparty', order: 'asc'}, account
        );
        return new GroupByCounterpartyDataSource(paginationDataSource, isExpense);
    }


    saveTransaction(transaction: Transaction) {
        this.appService.saveTransaction(transaction)
    }

    setCategory(row: (Transaction | GroupBy), selectedCategoryQualifiedNameStr: string) {
        // Get the SimpleCategory object from the CategoryMap
        const category = this.categoryMap.getSimpleCategory(selectedCategoryQualifiedNameStr);

        // Check if row is an interface that has key 'isGroupBy'
        if ("isGroupBy" in row) {
            (row as GroupBy).transactions.forEach(transaction => {
                transaction.category = category;
                this.saveTransaction(transaction);
            });
            return;
        }
        else {
            let transaction = row as Transaction;
            transaction.category = category;
            this.saveTransaction(transaction);
        }
    }

    amountType(transaction: Transaction | GroupBy): AmountType {
        if ("isGroupBy" in transaction) {
            return transaction.isExpense ? AmountType.EXPENSES : AmountType.REVENUE;
        }
        if (transaction.amount === undefined || transaction.amount === null) {
            throw new Error("Amount is undefined or null");
        }
        return inferAmountType(transaction.amount)


    }

    isGroup(index: any, item: any): boolean {
        return item.isGroupBy;
    }

    onToggleChange($event: MatButtonToggleChange) {
        this.tableElement.nativeElement.scrollIntoView({behavior: 'smooth', block: 'start'});
        const value = $event.value;
        if (value === "expenses") {
            this.activeView.next(TransactionTypeEnum.EXPENSES);
        }
        else if (value === "revenue") {
            this.activeView.next(TransactionTypeEnum.REVENUE);
        }
        else {
            throw new Error("Unknown value " + value);
        }


    }
}
