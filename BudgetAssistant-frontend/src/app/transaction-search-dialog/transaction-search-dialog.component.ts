import { AfterViewInit, Component, Inject, OnInit, ViewChild } from '@angular/core';
import { MatLegacyDialogRef as MatDialogRef, MAT_LEGACY_DIALOG_DATA as MAT_DIALOG_DATA } from '@angular/material/legacy-dialog';
import {CategoryTreeDropdownComponent} from '../category-tree-dropdown/category-tree-dropdown.component';
import {AmountType, TransactionQuery, TransactionType} from '../model';
import { PeriodSelectionComponent } from '../period-selection/period-selection.component';
import { CounterpartyAccountNumberSelectionComponent } from '.././counterparty-account-number-selection/counterparty-account-number-selection.component';
import { CounterpartyNameSelectionComponent } from '.././counterparty-name-selection/counterparty-name-selection.component';
import { TransactionCommunicationsSearchComponent } from '../transaction-mededelingen-search/transaction-communications-search.component';
import { TransactiontypeSelectionComponent } from '../transactiontype-selection/transactiontype-selection.component';

@Component({
  selector: 'app-transaction-search-dialog',
  templateUrl: './transaction-search-dialog.component.html',
  styleUrls: ['./transaction-search-dialog.component.scss']
})
export class TransactionSearchDialogComponent implements OnInit, AfterViewInit {

  @ViewChild(TransactiontypeSelectionComponent) transactiontypeSelectionComponent!: TransactiontypeSelectionComponent;
  @ViewChild(PeriodSelectionComponent) periodSelection!: PeriodSelectionComponent;
  @ViewChild(CategoryTreeDropdownComponent) categorySelection!: CategoryTreeDropdownComponent;
  @ViewChild(CounterpartyNameSelectionComponent) tegenpartijSelection!: CounterpartyNameSelectionComponent;
  @ViewChild(CounterpartyAccountNumberSelectionComponent) tegenpartijRekeningSelection!: CounterpartyAccountNumberSelectionComponent;
  @ViewChild(TransactionCommunicationsSearchComponent) transactionMededelingenSearch!: TransactionCommunicationsSearchComponent;

  constructor(
    public dialogRef: MatDialogRef<TransactionSearchDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: TransactionQuery,
  ) {


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


  ngOnInit() {


  }






  currentQuery?: TransactionQuery;


  handleTransactionTypeSelectionChange() {
    let vType: TransactionType = this.transactiontypeSelectionComponent.selectedTransactionType;
    let vInkomsten: boolean = false;
    let vUitgaven: boolean = false;
    switch (vType) {
      case TransactionType.BOTH:
        vInkomsten = true;
        vUitgaven = false;
        break;
      case TransactionType.REVENUE:
        vInkomsten = true;
        break;
      case TransactionType.EXPENSES:
        vUitgaven = true;
        break;

    }
    if (this.currentQuery === undefined) {
      this.currentQuery = {
        revenue: vInkomsten,
        expenses: vUitgaven,
        counterpartyName: undefined,
        minAmount: undefined,
        maxAmount: undefined,
        accountNumber: undefined,
        category: undefined,
        freeText: undefined,
        counterpartyAccountNumber: undefined,
        startDate: undefined,
        endDate: undefined,
        transactionOrCommunication : undefined,
        uploadTimestamp: undefined


      }
    } else {
      this.currentQuery.revenue = vInkomsten;
      this.currentQuery.expenses = vUitgaven;

    }

  }

  handlePeriodSelectionChange(){
    let vStartDate: Date | null =this.periodSelection.range.controls.start.value;
    let vEndDate : Date | null = this.periodSelection.range.controls.end.value;


    if (this.currentQuery === undefined) {
      this.currentQuery = {
        revenue: undefined,
        expenses: undefined,
        counterpartyName: undefined,
        minAmount: undefined,
        maxAmount: undefined,
        accountNumber: undefined,
        category: undefined,
        freeText: undefined,
        counterpartyAccountNumber: undefined,
        startDate: vStartDate,
        endDate: vEndDate,
        transactionOrCommunication : undefined,
        uploadTimestamp: undefined

      }
    } else {
      this.currentQuery.startDate = vStartDate;
      this.currentQuery.endDate = vEndDate;

    }

  }
  handleCategorySelectionChange(){
    let vCategory: string | undefined  = this.categorySelection.selectedCategoryQualifiedNameStr;



    if (this.currentQuery === undefined) {
      this.currentQuery = {
        revenue: undefined,
        expenses: undefined,
        counterpartyName: undefined,
        minAmount: undefined,
        maxAmount: undefined,
        accountNumber: undefined,
        category: vCategory,
        freeText: undefined,
        counterpartyAccountNumber: undefined,
        startDate: undefined,
        endDate: undefined,
        transactionOrCommunication : undefined,
        uploadTimestamp: undefined

      }
    } else {
      this.currentQuery.category = vCategory
    }

  }
  handleTegenpartijSelectionChange(){
    let vTegenpartij: string | undefined  = this.tegenpartijSelection.selectedCounterpartyName;

    if (this.currentQuery === undefined) {
      this.currentQuery = {
        revenue: undefined,
        expenses: undefined,
        counterpartyName: vTegenpartij,
        minAmount: undefined,
        maxAmount: undefined,
        accountNumber: undefined,
        category: undefined,
        freeText: undefined,
        counterpartyAccountNumber: undefined,
        startDate: undefined,
        endDate: undefined,
        transactionOrCommunication : undefined,
        uploadTimestamp: undefined

      }
    } else {
      this.currentQuery.counterpartyName = vTegenpartij;
    }

  }

  handleRekeningTegenpartijSelectionChange(){
    let vRekeningTegenpartij: string | undefined  = this.tegenpartijRekeningSelection.selectedCounterpartAccountNumber;

    if (this.currentQuery === undefined) {
      this.currentQuery = {
        revenue: undefined,
        expenses: undefined,
        counterpartyName: undefined,
        minAmount: undefined,
        maxAmount: undefined,
        accountNumber: undefined,
        category: undefined,
        freeText: undefined,
        counterpartyAccountNumber: vRekeningTegenpartij,
        startDate: undefined,
        endDate: undefined,
        transactionOrCommunication : undefined,
        uploadTimestamp: undefined

      }
    } else {
      this.currentQuery.counterpartyAccountNumber = vRekeningTegenpartij;
    }

  }

  handleTransactionMededelingenSearchChange(){
    let vSearchText: string | undefined  = this.transactionMededelingenSearch.searchText;

    if (this.currentQuery === undefined) {
      this.currentQuery = {
        revenue: undefined,
        expenses: undefined,
        counterpartyName: undefined,
        minAmount: undefined,
        maxAmount: undefined,
        accountNumber: undefined,
        category: undefined,
        freeText: undefined,
        counterpartyAccountNumber: undefined,
        startDate: undefined,
        endDate: undefined,
        transactionOrCommunication : vSearchText,
        uploadTimestamp: undefined

      }
    } else {
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
