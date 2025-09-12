import {ChangeDetectorRef, Component, effect, ElementRef, OnInit, ViewChild} from '@angular/core';
import {MatPaginator, PageEvent} from "@angular/material/paginator";
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
import {BehaviorSubject} from "rxjs";
import {MatButtonToggle, MatButtonToggleChange, MatButtonToggleGroup} from "@angular/material/button-toggle";
import {BankAccount, Transaction, TransactionTypeEnum} from "@daanvdn/budget-assistant-client";
import {AmountType, CategoryMap, GroupBy, inferAmountType, TransactionTypeAndBankAccount} from "../model";
import {MatToolbar} from '@angular/material/toolbar';
import {BankAccountSelectionComponent} from '../bank-account-selection/bank-account-selection.component';
import {AsyncPipe, NgIf} from '@angular/common';
import {CategoryTreeDropdownComponent} from '../category-tree-dropdown/category-tree-dropdown.component';
import {TanstackPaginatedDataSource} from "../tanstack-paginated-datasource";
import {AppService} from "../app.service";


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
    @ViewChild(MatTable) table!: MatTable<Transaction | GroupBy>;
    @ViewChild('table', {read: ElementRef, static: false}) tableElement!: ElementRef;


    datasource: TanstackPaginatedDataSource<Transaction | GroupBy, TransactionTypeAndBankAccount> = this.initDataSource();
    categoryMap!: CategoryMap;
    public toggleValue = 'expenses';


    private bankAccount!: BankAccount;
    displayedColumns = [
        "transaction",
        "amount",
        "category"
    ];
    private activeView: BehaviorSubject<TransactionTypeEnum> = new BehaviorSubject<TransactionTypeEnum>(
        TransactionTypeEnum.EXPENSES);
    private activeViewObservable = this.activeView.asObservable();

    expensesPageIndex = 0;
    expensesPageSize = 10;
    revenuePageIndex = 0;
    revenuePageSize = 10;

    constructor(private appService: AppService, private cdr: ChangeDetectorRef) {

        effect(() => {
            const selectedBankAccount = this.appService.selectedBankAccount();
            if (selectedBankAccount) {
                this.bankAccount = selectedBankAccount;
                // Trigger initial data load for current view
                const currentView: TransactionTypeEnum = this.activeView.getValue();
                const query: TransactionTypeAndBankAccount = {
                    bankAccount: this.bankAccount,
                    transactionType: currentView
                };

                let currentPageIndex: number | undefined =undefined;
                let currentPageSize: number | undefined =undefined;
                switch (currentView) {
                    case TransactionTypeEnum.EXPENSES:
                        currentPageIndex = this.expensesPageIndex;
                        currentPageSize = this.expensesPageSize;
                        break;
                    case TransactionTypeEnum.REVENUE:
                        currentPageIndex = this.revenuePageIndex;
                        currentPageSize = this.revenuePageSize;
                        break;
                    default:
                        throw new Error("Unknown active view: " + currentView);
                }
                this.datasource.setPage(currentPageIndex, currentPageSize);
                this.datasource.setQuery(query);

            }

        }, {allowSignalWrites: true});

        effect(() => {

            const categoryMap = this.appService.categoryMap();
            if (categoryMap) {
                this.categoryMap = categoryMap;
            }
        }, {allowSignalWrites: true});


        this.activeViewObservable.subscribe(currentView => {
                if (currentView) {
                    if (this.bankAccount) {

                        const currentView: TransactionTypeEnum = this.activeView.getValue();
                        const query: TransactionTypeAndBankAccount = {
                            bankAccount: this.bankAccount,
                            transactionType: currentView
                        };

                        let currentPageIndex: number | undefined =undefined;
                        let currentPageSize: number | undefined =undefined;
                        switch (currentView) {
                            case TransactionTypeEnum.EXPENSES:
                                currentPageIndex = this.expensesPageIndex;
                                currentPageSize = this.expensesPageSize;
                                break;
                            case TransactionTypeEnum.REVENUE:
                                currentPageIndex = this.revenuePageIndex;
                                currentPageSize = this.revenuePageSize;
                                break;
                            default:
                                throw new Error("Unknown active view: " + currentView);
                        }
                        this.datasource.setPage(currentPageIndex, currentPageSize);
                        this.datasource.setQuery(query);

                    }


                }

            }
        )
    }


    ngOnInit(): void {
    }

    private initDataSource(): TanstackPaginatedDataSource<Transaction | GroupBy, TransactionTypeAndBankAccount> {
        return new TanstackPaginatedDataSource<Transaction | GroupBy, TransactionTypeAndBankAccount>(
            params => this.appService.pageTransactionsToManuallyReview(params), 1000 * 60 * 5
        )

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
        this.toggleValue = value;
        let activeView = undefined;

        switch (value) {
            case "expenses":
                activeView = TransactionTypeEnum.EXPENSES;
                this.activeView.next(activeView);
                break;
            case "revenue":
                activeView = TransactionTypeEnum.REVENUE;
                this.activeView.next(activeView);
                break;
            default:
                throw new Error("Unknown value: " + value);
        }
        if (!activeView) {
            return;
        }


    }

    onPageEvent(event: PageEvent): void {
        this.setPageIndex(event.pageIndex);
        this.setPageSize(event.pageSize);
        this.datasource.setPage(event.pageIndex, event.pageSize);
    }

    getPageIndex(): number {
        switch (this.activeView.getValue()) {
            case TransactionTypeEnum.EXPENSES:
                return this.expensesPageIndex;
            case TransactionTypeEnum.REVENUE:
                return this.revenuePageIndex;
            default:
                throw new Error("Unknown active view: " + this.activeView.getValue());
        }

    }

    getPageSize(): number {
        switch (this.activeView.getValue()) {
            case TransactionTypeEnum.EXPENSES:
                return this.expensesPageSize;
            case TransactionTypeEnum.REVENUE:
                return this.revenuePageSize;
            default:
                throw new Error("Unknown active view: " + this.activeView.getValue());
        }
    }

    setPageSize(size: number): void {
        switch (this.activeView.getValue()) {
            case TransactionTypeEnum.EXPENSES:
                this.expensesPageSize = size;
                break;
            case TransactionTypeEnum.REVENUE:
                this.revenuePageSize = size;
                break;
            default:
                throw new Error("Unknown active view: " + this.activeView.getValue());
        }

    }

    setPageIndex(index: number): void {
        switch (this.activeView.getValue()) {
            case TransactionTypeEnum.EXPENSES:
                this.expensesPageIndex = index;
                break;
            case TransactionTypeEnum.REVENUE:
                this.revenuePageIndex = index;
                break;
            default:
                throw new Error("Unknown active view: " + this.activeView.getValue());

        }
    }

}
