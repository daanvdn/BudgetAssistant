import {AfterViewInit, Component, effect, Inject, OnInit, ViewChild} from '@angular/core';
import {
    MAT_DIALOG_DATA,
    MatDialogActions,
    MatDialogContent,
    MatDialogRef,
    MatDialogTitle
} from '@angular/material/dialog';
import {CategoryTreeDropdownComponent} from '../category-tree-dropdown/category-tree-dropdown.component';
import {AmountType, CategoryMap} from '../model';
import {PeriodSelectionComponent} from '../period-selection/period-selection.component';
import {
    CounterpartyAccountNumberSelectionComponent,
    CounterpartyAccountNumberSelectionComponent as CounterpartyAccountNumberSelectionComponent_1
} from '../counterparty-account-number-selection/counterparty-account-number-selection.component';
import {
    CounterpartyNameSelectionComponent,
    CounterpartyNameSelectionComponent as CounterpartyNameSelectionComponent_1
} from '../counterparty-name-selection/counterparty-name-selection.component';
import {
    TransactionCommunicationsSearchComponent
} from '../transaction-mededelingen-search/transaction-communications-search.component';
import {MatButton} from '@angular/material/button';
import {TransactionQuery, TransactionTypeEnum} from "@daanvdn/budget-assistant-client";
import {AppService} from "../app.service";
import {MatFormField, MatLabel} from "@angular/material/form-field";
import {MatInput} from "@angular/material/input";
import {MatOption} from "@angular/material/core";
import {MatSelect, MatSelectChange} from "@angular/material/select";
import {NgForOf} from "@angular/common";
import {PaginatorModule} from "primeng/paginator";

@Component({
    selector: 'app-transaction-search-dialog',
    templateUrl: './transaction-search-dialog.component.html',
    styleUrls: ['./transaction-search-dialog.component.scss'],
    standalone: true,
    imports: [MatDialogTitle, MatDialogContent, PeriodSelectionComponent,
        CategoryTreeDropdownComponent, CounterpartyNameSelectionComponent_1, CounterpartyAccountNumberSelectionComponent_1,
        TransactionCommunicationsSearchComponent, MatDialogActions, MatButton, MatFormField, MatInput, MatLabel, MatOption, MatSelect, NgForOf, PaginatorModule]
})
export class TransactionSearchDialogComponent implements OnInit, AfterViewInit {

    @ViewChild(PeriodSelectionComponent) periodSelection!: PeriodSelectionComponent;
    @ViewChild(CategoryTreeDropdownComponent) categorySelection!: CategoryTreeDropdownComponent;
    @ViewChild(CounterpartyNameSelectionComponent) counterpartNameSelection!: CounterpartyNameSelectionComponent;
    @ViewChild(
        CounterpartyAccountNumberSelectionComponent) accountNumberCounterpartySelection!: CounterpartyAccountNumberSelectionComponent;
    @ViewChild(
        TransactionCommunicationsSearchComponent) transactionCommunicationsSearch!: TransactionCommunicationsSearchComponent;
    transactionTypes: Map<string, TransactionTypeEnum> = new Map<string, TransactionTypeEnum>();
    transactionTypeKeys: string[] = [];
    transactionType?: TransactionTypeEnum;
    minAmount?: number;
    maxAmount?: number;
    startDate?: Date;
    endDate?: Date;
    categoryId?: number;
    counterpartyName?: string;
    counterpartAccountNumber?: string;
    transactionOrCommunication?: string;


    private categoryMap?: CategoryMap;

    constructor(
        public dialogRef: MatDialogRef<TransactionSearchDialogComponent>,
        @Inject(MAT_DIALOG_DATA) public data: TransactionQuery, private appService: AppService) {
        effect(() => {

            const categoryMap = this.appService.categoryMap();
            if (categoryMap) {
                this.categoryMap = categoryMap;
            }
        });
        this.transactionTypes.set("in- & uitkomsten", TransactionTypeEnum.BOTH)
        this.transactionTypes.set("uitgaven", TransactionTypeEnum.EXPENSES)
        this.transactionTypes.set("inkomsten", TransactionTypeEnum.REVENUE)
        this.transactionTypeKeys = Array.from(this.transactionTypes.keys());


    }

    ngAfterViewInit(): void {
        /**
         * logic to make dialog scroll to top
         */
        let element: Element | null = document.querySelector("#first");
        if (element !== null) {
            element.scrollIntoView(true);
        }
    }


    ngOnInit() {


    }


  private dateToString(date: Date | null): string | undefined {
        if (date === null) {
            return undefined;
        }
        return date.toISOString().split('T')[0];
    }

    handlePeriodSelectionChange() {


        this.startDate = this.periodSelection.range.controls.start.value ?? undefined;
        this.endDate = this.periodSelection.range.controls.end.value ?? undefined;


    }

    handleCategorySelectionChange() {
        let vCategory: string | undefined = this.categorySelection.selectedCategoryQualifiedNameStr;
        if (this.categoryMap === undefined) {
            throw new Error("Category map is undefined");
        }
        if (vCategory === undefined) {
            console.warn("Category is undefined");
            return;
        }
        this.categoryId = this.categoryMap.getId(vCategory);

    }

    handleCounterpartySelectionChange() {
        this.counterpartyName = this.counterpartNameSelection.selectedCounterpartyName;
    }

    handleCounterpartyAccountSelectionChange() {
        this.counterpartAccountNumber = this.accountNumberCounterpartySelection.selectedCounterpartAccountNumber;


    }

    handleTransactionCommunicationsSearchChange() {
        this.transactionOrCommunication = this.transactionCommunicationsSearch.searchText;

    }


    onCancelClick(): void {
        this.dialogRef.close();
    }

    onSearchClick(): void {
        const query: TransactionQuery = {
            transactionType: this.transactionType,
            counterpartyName: this.counterpartyName,
            minAmount: this.minAmount,
            maxAmount: this.maxAmount,
            accountNumber: undefined,
            counterpartyAccountNumber: this.counterpartAccountNumber,
            startDate: this.startDate ? this.dateToString(this.startDate) : undefined,
            endDate: this.endDate ? this.dateToString(this.endDate) : undefined,
            transactionOrCommunication: this.transactionOrCommunication,
            uploadTimestamp: undefined


        }

        this.dialogRef.close(query);
    }

    protected readonly AmountType = AmountType;

    handleTransactionTypeChange(event: MatSelectChange) {
        this.transactionType =  this.transactionTypes.get(event.value);
    }
}
