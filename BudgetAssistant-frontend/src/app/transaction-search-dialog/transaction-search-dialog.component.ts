import {AfterViewInit, Component, Inject, OnInit, ViewChild} from '@angular/core';
import {
    MatDialogRef,
    MAT_DIALOG_DATA,
    MatDialogTitle,
    MatDialogContent,
    MatDialogActions
} from '@angular/material/dialog';
import {CategoryTreeDropdownComponent} from '../category-tree-dropdown/category-tree-dropdown.component';
import {AmountType, TransactionType} from '../model';
import {PeriodSelectionComponent} from '../period-selection/period-selection.component';
import {
    CounterpartyAccountNumberSelectionComponent
} from '../counterparty-account-number-selection/counterparty-account-number-selection.component';
import {
    CounterpartyNameSelectionComponent
} from '../counterparty-name-selection/counterparty-name-selection.component';
import {
    TransactionCommunicationsSearchComponent
} from '../transaction-mededelingen-search/transaction-communications-search.component';
import {TransactiontypeSelectionComponent} from '../transactiontype-selection/transactiontype-selection.component';
import {
    CounterpartyNameSelectionComponent as CounterpartyNameSelectionComponent_1
} from '../counterparty-name-selection/counterparty-name-selection.component';
import {
    CounterpartyAccountNumberSelectionComponent as CounterpartyAccountNumberSelectionComponent_1
} from '../counterparty-account-number-selection/counterparty-account-number-selection.component';
import {MatButton} from '@angular/material/button';
import {CategoryIndex, TransactionQuery, TransactionTypeEnum} from "@daanvdn/budget-assistant-client";
import {AppService} from "../app.service";

@Component({
    selector: 'app-transaction-search-dialog',
    templateUrl: './transaction-search-dialog.component.html',
    styleUrls: ['./transaction-search-dialog.component.scss'],
    standalone: true,
    imports: [MatDialogTitle, MatDialogContent, TransactiontypeSelectionComponent, PeriodSelectionComponent,
        CategoryTreeDropdownComponent, CounterpartyNameSelectionComponent_1, CounterpartyAccountNumberSelectionComponent_1,
        TransactionCommunicationsSearchComponent, MatDialogActions, MatButton]
})
export class TransactionSearchDialogComponent implements OnInit, AfterViewInit {

    @ViewChild(TransactiontypeSelectionComponent) transactiontypeSelectionComponent!: TransactiontypeSelectionComponent;
    @ViewChild(PeriodSelectionComponent) periodSelection!: PeriodSelectionComponent;
    @ViewChild(CategoryTreeDropdownComponent) categorySelection!: CategoryTreeDropdownComponent;
    @ViewChild(CounterpartyNameSelectionComponent) tegenpartijSelection!: CounterpartyNameSelectionComponent;
    @ViewChild(
        CounterpartyAccountNumberSelectionComponent) accountNumberCounterpartySelection!: CounterpartyAccountNumberSelectionComponent;
    @ViewChild(
        TransactionCommunicationsSearchComponent) transactionCommunicationsSearch!: TransactionCommunicationsSearchComponent;

    private categoryIndex?: CategoryIndex;

    constructor(
        public dialogRef: MatDialogRef<TransactionSearchDialogComponent>,
        @Inject(MAT_DIALOG_DATA) public data: TransactionQuery, private appService: AppService) {
        this.appService.categoryIndexObservable$.subscribe((categoryIndex: CategoryIndex | undefined) => {
            this.categoryIndex = categoryIndex;

        });


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


    currentQuery?: TransactionQuery;


    handleTransactionTypeSelectionChange() {
        let vType: TransactionTypeEnum = this.transactiontypeSelectionComponent.selectedTransactionType;

        if (this.currentQuery === undefined) {
            this.currentQuery = {
                transactionType: vType,
                counterpartyName: undefined,
                minAmount: undefined,
                maxAmount: undefined,
                accountNumber: undefined,
                counterpartyAccountNumber: undefined,
                startDate: undefined,
                endDate: undefined,
                transactionOrCommunication: undefined,
                uploadTimestamp: undefined


            }
        }
        else {
            this.currentQuery.transactionType = vType;
        }

    }

    handlePeriodSelectionChange() {

        function dateToString(date: Date | null): string | undefined {
            if (date === null) {
                return undefined;
            }
            return date.toISOString().split('T')[0];
        }

        let vStartDate: Date | null = this.periodSelection.range.controls.start.value;
        let vEndDate: Date | null = this.periodSelection.range.controls.end.value;


        if (this.currentQuery === undefined) {
            this.currentQuery = {
                transactionType: undefined,
                counterpartyName: undefined,
                minAmount: undefined,
                maxAmount: undefined,
                accountNumber: undefined,
                categoryId: undefined,
                transactionOrCommunication: undefined,
                counterpartyAccountNumber: undefined,
                startDate: dateToString(vStartDate),
                endDate: dateToString(vEndDate),
                uploadTimestamp: undefined,
                manuallyAssignedCategory: undefined
            }

        }
        else {
            this.currentQuery.startDate = dateToString(vStartDate);
            this.currentQuery.endDate = dateToString(vEndDate);

        }

    }

    handleCategorySelectionChange() {
        let vCategory: string | undefined = this.categorySelection.selectedCategoryQualifiedNameStr;
        if (this.categoryIndex === undefined) {
            throw new Error("Category index is undefined");
        }
        if (vCategory === undefined) {
            console.warn("Category is undefined");
            return;
        }
        let categoryId: number | undefined = this.categoryIndex.qualifiedNameToIdIndex[vCategory];
        if (categoryId === undefined) {
            throw new Error("Category not found: " + vCategory);
        }


        if (this.currentQuery === undefined) {
            this.currentQuery = {
                transactionType: undefined,
                counterpartyName: undefined,
                minAmount: undefined,
                maxAmount: undefined,
                accountNumber: undefined,
                categoryId: categoryId,
                transactionOrCommunication: undefined,
                counterpartyAccountNumber: undefined,
                startDate: undefined,
                endDate: undefined,
                uploadTimestamp: undefined,
                manuallyAssignedCategory: undefined

            }
        }
        else {
            this.currentQuery.categoryId = categoryId;
        }

    }

    handleTegenpartijSelectionChange() {
        let vTegenpartij: string | undefined = this.tegenpartijSelection.selectedCounterpartyName;

        if (this.currentQuery === undefined) {
            this.currentQuery = {
                counterpartyName: vTegenpartij,
                minAmount: undefined,
                maxAmount: undefined,
                accountNumber: undefined,
                counterpartyAccountNumber: undefined,
                startDate: undefined,
                endDate: undefined,
                transactionOrCommunication: undefined,
                uploadTimestamp: undefined


            }
        }
        else {
            this.currentQuery.counterpartyName = vTegenpartij;
        }

    }

    handleRekeningTegenpartijSelectionChange() {
        let vAccountNumberCounterparty: string | undefined = this.accountNumberCounterpartySelection.selectedCounterpartAccountNumber;

        if (this.currentQuery === undefined) {
            this.currentQuery = {
                counterpartyName: undefined,
                minAmount: undefined,
                maxAmount: undefined,
                accountNumber: undefined,
                counterpartyAccountNumber: vAccountNumberCounterparty,
                startDate: undefined,
                endDate: undefined,
                transactionOrCommunication: undefined,
                uploadTimestamp: undefined

            }
        }
        else {
            this.currentQuery.counterpartyAccountNumber = vAccountNumberCounterparty;
        }

    }

    handleTransactionCommunicationsSearchChange() {
        let vSearchText: string | undefined = this.transactionCommunicationsSearch.searchText;

        if (this.currentQuery === undefined) {
            this.currentQuery = {
                counterpartyName: undefined,
                minAmount: undefined,
                maxAmount: undefined,
                accountNumber: undefined,
                counterpartyAccountNumber: undefined,
                startDate: undefined,
                endDate: undefined,
                transactionOrCommunication: vSearchText,
                uploadTimestamp: undefined

            }
        }
        else {
            this.currentQuery.transactionOrCommunication = vSearchText;
        }

    }

    onCancelClick(): void {
        this.dialogRef.close();
    }

    onSearchClick(): void {
        this.dialogRef.close(this.currentQuery);
    }

    protected readonly AmountType = AmountType;
}
