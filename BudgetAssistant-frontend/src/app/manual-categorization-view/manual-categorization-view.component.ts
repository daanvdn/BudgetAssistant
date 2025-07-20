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
import {
    BankAccount,
    PageTransactionsToManuallyReviewRequest,
    Transaction,
    TransactionTypeEnum
} from "@daanvdn/budget-assistant-client";
import {AmountType, CategoryMap, GroupBy, inferAmountType, TransactionTypeAndBankAccount} from "../model";
import {MatToolbar} from '@angular/material/toolbar';
import {BankAccountSelectionComponent} from '../bank-account-selection/bank-account-selection.component';
import {AsyncPipe, NgIf} from '@angular/common';
import {CategoryTreeDropdownComponent} from '../category-tree-dropdown/category-tree-dropdown.component';
import {TanstackPaginatedDataSource} from "../tanstack-paginated-datasource";


@Component({
    selector: 'app-manual-categorization-view',
    templateUrl: './manual-categorization-view.component.html',
    styleUrls: ['./manual-categorization-view.component.scss'],
    standalone: true,
    imports: [MatToolbar, BankAccountSelectionComponent, MatButtonToggleGroup, MatButtonToggle, NgIf,
        MatPaginator, MatTable, MatColumnDef, MatHeaderCellDef, MatHeaderCell, MatCellDef, MatCell,
        CategoryTreeDropdownComponent, MatHeaderRowDef, MatHeaderRow, MatRowDef, MatRow]
})
export class ManualCategorizationViewComponent implements OnInit {

    @ViewChild(MatPaginator, {static: false}) paginator!: MatPaginator;
    @ViewChild(MatSort, {static: false}) sort!: MatSort;
    @ViewChild(MatTable) table!: MatTable<Transaction>;
    @ViewChild('table', {read: ElementRef, static: false}) tableElement!: ElementRef;


    expensesDataSource: TanstackPaginatedDataSource<Transaction | GroupBy, TransactionTypeAndBankAccount> = this.initDataSource();
    revenueDataSource: TanstackPaginatedDataSource<Transaction | GroupBy, TransactionTypeAndBankAccount> = this.initDataSource();
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
            }
        });

        effect(() => {

            const categoryMap = this.appService.categoryMap();
            if (categoryMap) {
                this.categoryMap = categoryMap;
            }
        });


        this.activeViewObservable.subscribe(activeView => {
                if (activeView) {
                    if (this.bankAccount) {
                        let query: TransactionTypeAndBankAccount = {
                            bankAccount: this.bankAccount,
                            transactionType: activeView
                        }
                        if (activeView === TransactionTypeEnum.EXPENSES) {
                            this.expensesDataSource.setQuery(query);

                        }else if (activeView === TransactionTypeEnum.REVENUE) {
                            this.revenueDataSource.setQuery(query);

                        } else {
                            throw new Error("Unknown active view: " + activeView);
                        }
                    }


                }

            }
        )

    }

    public getDataSource(): TanstackPaginatedDataSource<Transaction | GroupBy, TransactionTypeAndBankAccount> {
        const value = this.activeView.getValue();
        if (value === TransactionTypeEnum.EXPENSES) {
            return this.expensesDataSource;
        }
        else if (value === TransactionTypeEnum.REVENUE) {
            return this.revenueDataSource;
        }
        else {
            throw new Error("Unknown active view: " + value);
        }
    }

    ngOnInit(): void {
    }

    private initDataSource(): TanstackPaginatedDataSource<Transaction | GroupBy, TransactionTypeAndBankAccount> {
        return new TanstackPaginatedDataSource<Transaction | GroupBy, TransactionTypeAndBankAccount>(
            params => this.appService.pageTransactionsToManuallyReview(params), 1000 * 60 * 5
        )

    }


    saveTransaction(transaction:Transaction) {
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

    amountType(transaction: Transaction | GroupBy):
        AmountType {
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

    protected readonly TanstackPaginatedDataSource = TanstackPaginatedDataSource;
}
