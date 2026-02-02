import {Component, OnInit} from '@angular/core';
import {faSearch} from "@fortawesome/free-solid-svg-icons/faSearch";
import {BankAccountRead, Grouping, TransactionTypeEnum} from "@daanvdn/budget-assistant-client";
import {MatToolbar} from '@angular/material/toolbar';
import {MatIconButton} from '@angular/material/button';
import {FaIconComponent} from '@fortawesome/angular-fontawesome';
import {MatTab, MatTabGroup} from '@angular/material/tabs';
import {NgIf} from '@angular/common';
import {CriteriaToolbarComponent} from '../criteria-toolbar/criteria-toolbar.component';
import {ExpensesRevenueComponent} from '../revenue-expenses/revenue-expenses.component';
import {
    RevenueExpensesPerPeriodAndCategoryComponent
} from '../revenue-expenses-per-period-and-category/revenue-expenses-per-period-and-category.component';
import {CategoryDetailsComponent} from '../category-details/category-details.component';
import {BudgetTrackingComponent} from '../budget-tracking/budget-tracking.component';
import {Criteria} from '../model/criteria.model';



@Component({
    selector: 'insights', templateUrl: './insights.component.html', styleUrls: ['./insights.component.scss'],
    standalone: true,
    imports: [MatToolbar, MatIconButton, FaIconComponent, MatTabGroup, MatTab, NgIf, CriteriaToolbarComponent, ExpensesRevenueComponent, RevenueExpensesPerPeriodAndCategoryComponent, CategoryDetailsComponent, BudgetTrackingComponent]
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
