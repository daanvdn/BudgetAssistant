import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';
import {faXmark} from "@fortawesome/free-solid-svg-icons";
import {anyIsUndefinedOrEmpty} from "../model";
import {Criteria} from "../model/criteria.model";
import {BankAccount, GroupingEnum, TransactionTypeEnum} from "@daanvdn/budget-assistant-client";
import {NgIf} from '@angular/common';
import {BankAccountSelectionComponent} from '../bank-account-selection/bank-account-selection.component';
import {GroupingTypeSelectionComponent} from '../grouping-type-selection/grouping-type-selection.component';
import {PeriodSelectionComponent} from '../period-selection/period-selection.component';
import {ExpensesRevenueToggleComponent} from '../expenses-revenue-toggle/expenses-revenue-toggle.component';
import {MatButton} from '@angular/material/button';
import {FaIconComponent} from '@fortawesome/angular-fontawesome';


@Component({
    selector: 'criteria-toolbar',
    templateUrl: './criteria-toolbar.component.html',
    styleUrls: ['./criteria-toolbar.component.scss'],
    standalone: true,
    imports: [NgIf, BankAccountSelectionComponent, GroupingTypeSelectionComponent, PeriodSelectionComponent, ExpensesRevenueToggleComponent, MatButton, FaIconComponent]
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
    grouping!: GroupingEnum ;
    startDate!: Date;
    endDate!: Date;
    transactionType!: TransactionTypeEnum;
    currentCriteria!: Criteria;


    constructor() {

    }

    ngOnInit(): void {
    }

    onClickClose() {
        this.closed.emit(true);
    }

    protected readonly faXmark = faXmark;


    onExpensesRevenueChange(transactionType: TransactionTypeEnum) {
        this.transactionType = transactionType;
        this.maybeEmitCriteriaChange();
    }

    onBankAccountChange(bankAccount: BankAccount) {
        this.bankAccount = bankAccount;
        this.maybeEmitCriteriaChange();
    }

    onGroupingChange(grouping: GroupingEnum) {
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
