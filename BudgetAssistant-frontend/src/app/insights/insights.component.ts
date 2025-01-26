import {Component, OnInit} from '@angular/core';
import {faSearch} from "@fortawesome/free-solid-svg-icons/faSearch";
import {BankAccount, Grouping, TransactionType} from "../model";


export class Criteria {
    bankAccount: BankAccount;
    grouping: Grouping;
    startDate: Date;
    endDate: Date;
    transactionType: TransactionType | undefined;

    constructor(bankAccount: BankAccount, grouping: Grouping, startDate: Date, endDate: Date,
                transactionType: TransactionType | undefined) {
        this.bankAccount = bankAccount;
        this.grouping = grouping;
        this.startDate = startDate;
        this.endDate = endDate;
        this.transactionType = transactionType;
    }

    public equals(criteria: Criteria): boolean {

        if (!criteria || !criteria.bankAccount || !criteria.grouping || !criteria.startDate || !criteria.endDate) {
            return false;
        }
        if (this.transactionType !== criteria.transactionType) {
            return false;
        }
        return this.bankAccount.accountNumber === criteria.bankAccount.accountNumber &&
            this.grouping === criteria.grouping &&
            this.startDate === criteria.startDate &&
            this.endDate === criteria.endDate &&
            this.transactionType === criteria.transactionType;

    }
}



@Component({
    selector: 'insights', templateUrl: './insights.component.html', styleUrls: ['./insights.component.scss']

})
export class InsightsComponent implements OnInit {

    showCriteriaToolbar: boolean = true;

    constructor() {

    }


    ngOnInit() {


    }

    protected readonly faSearch = faSearch;

    onClosed() {
        this.showCriteriaToolbar = false;
    }

    getDynamicHeight(): string {
        if (this.showCriteriaToolbar) {
            return "75vh";
        }

        return "85vh";
    }


    expensesRevenueCriteria!: Criteria;
    categoryDetailsCriteria!: Criteria;
    categoryOverviewCriteria!: Criteria;
    budgetTrackingCriteria!: Criteria;
}
