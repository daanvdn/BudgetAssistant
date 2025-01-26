import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';
import {faXmark} from "@fortawesome/free-solid-svg-icons";
import {anyIsUndefinedOrEmpty, BankAccount, Grouping, TransactionType} from "../model";
import {Criteria} from "../insights/insights.component";


@Component({
    selector: 'criteria-toolbar',
    templateUrl: './criteria-toolbar.component.html',
    styleUrls: ['./criteria-toolbar.component.scss']
})
export class CriteriaToolbarComponent implements OnInit {

    @Input() enableBankAccountSelection: boolean = true;
    @Input() enableGroupingTypeSelection: boolean = true;
    @Input() enablePeriodSelection: boolean = true;
    @Input() enableExpensesRevenueToggle: boolean = true;
    @Input() enableCloseButton: boolean = true;
    @Output() closed = new EventEmitter<boolean>();
    @Output() criteriaChange = new EventEmitter<Criteria>();


    bankAccount!: BankAccount;
    grouping!: Grouping;
    startDate!: Date;
    endDate!: Date;
    transactionType!: TransactionType;
    currentCriteria!: Criteria;


    constructor() {

    }

    ngOnInit(): void {
    }

    onClickClose() {
        this.closed.emit(true);
    }

    protected readonly faXmark = faXmark;


    onExpensesRevenueChange(transactionType: TransactionType) {
        this.transactionType = transactionType;
        this.maybeEmitCriteriaChange();
    }

    onBankAccountChange(bankAccount: BankAccount) {
        this.bankAccount = bankAccount;
        this.maybeEmitCriteriaChange();
    }

    onGroupingChange(grouping: Grouping) {
        this.grouping = grouping;
        this.maybeEmitCriteriaChange();
    }

    onPeriodChange($event: Date[]) {
        this.startDate = $event[0];
        this.endDate = $event[1];
        this.maybeEmitCriteriaChange();
    }

    requiredFieldsAreSet(): boolean {
        if (this.enableExpensesRevenueToggle && anyIsUndefinedOrEmpty(this.transactionType)) {
            return false;
        }
        if (this.enableBankAccountSelection && anyIsUndefinedOrEmpty(this.bankAccount)) {
            return false;
        }
        if (this.enableGroupingTypeSelection && anyIsUndefinedOrEmpty(this.grouping)) {
            return false;
        }
        if (this.enablePeriodSelection && anyIsUndefinedOrEmpty(this.startDate, this.endDate)) {
            return false;
        }

        return true;

    }


    maybeEmitCriteriaChange() {
        if (!this.requiredFieldsAreSet()) {
            return;
        }
        let criteria = new Criteria(this.bankAccount, this.grouping, this.startDate, this.endDate,
            this.transactionType);
        if (!this.currentCriteria) {
            this.currentCriteria = criteria;
            this.criteriaChange.emit(this.currentCriteria);

        }
        else if (!this.currentCriteria.equals(criteria)) {
            this.currentCriteria = criteria;
            this.criteriaChange.emit(this.currentCriteria);

        }
    }


}
