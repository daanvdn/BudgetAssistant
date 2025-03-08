import {NgModule} from '@angular/core';
import {BrowserModule} from '@angular/platform-browser';
import {AppRoutingModule} from './app-routing.module';
import {AppComponent} from './app.component';
import {BrowserAnimationsModule} from '@angular/platform-browser/animations';
import {FormsModule, ReactiveFormsModule} from '@angular/forms';
import { HTTP_INTERCEPTORS, provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
import {A11yModule} from '@angular/cdk/a11y';
import {CdkAccordionModule} from '@angular/cdk/accordion';
import {ClipboardModule} from '@angular/cdk/clipboard';
import {DragDropModule} from '@angular/cdk/drag-drop';
import {PortalModule} from '@angular/cdk/portal';
import {ScrollingModule} from '@angular/cdk/scrolling';
import {CdkStepperModule} from '@angular/cdk/stepper';
import {CdkTableModule} from '@angular/cdk/table';
import {CdkTreeModule} from '@angular/cdk/tree';
import {MatAutocompleteModule} from '@angular/material/autocomplete';
import {MatBadgeModule} from '@angular/material/badge';
import {MatBottomSheetModule} from '@angular/material/bottom-sheet';
import {MatButtonModule} from '@angular/material/button';
import {MatButtonToggleModule} from '@angular/material/button-toggle';
import {MatCardModule} from '@angular/material/card';
import {MatCheckboxModule} from '@angular/material/checkbox';
import {MatChipsModule} from '@angular/material/chips';
import {MatStepperModule} from '@angular/material/stepper';
import {MatDatepickerModule} from '@angular/material/datepicker';
import {MatDialogModule} from '@angular/material/dialog';
import {MatDividerModule} from '@angular/material/divider';
import {MatExpansionModule} from '@angular/material/expansion';
import {MatGridListModule} from '@angular/material/grid-list';
import {MatIconModule} from '@angular/material/icon';
import {MatInputModule} from '@angular/material/input';
import {MatListModule} from '@angular/material/list';
import {MatMenuModule} from '@angular/material/menu';
import {MatNativeDateModule, MatRippleModule} from '@angular/material/core';
import {MatPaginatorModule} from '@angular/material/paginator';
import {MatProgressBarModule} from '@angular/material/progress-bar';
import {MatProgressSpinnerModule} from '@angular/material/progress-spinner';
import {MatRadioModule} from '@angular/material/radio';
import {MatSelectModule} from '@angular/material/select';
import {MatSidenavModule} from '@angular/material/sidenav';
import {MatSliderModule} from '@angular/material/slider';
import {MatSlideToggleModule} from '@angular/material/slide-toggle';
import {MatSnackBarModule} from '@angular/material/snack-bar';
import {MatSortModule} from '@angular/material/sort';
import {MatTableModule} from '@angular/material/table';
import {MatTabsModule} from '@angular/material/tabs';
import {MatToolbarModule} from '@angular/material/toolbar';
import {MatTooltipModule} from '@angular/material/tooltip';
import {MatTreeModule} from '@angular/material/tree';
import {OverlayModule} from '@angular/cdk/overlay';
import {CdkMenuModule} from '@angular/cdk/menu';
import {DialogModule} from '@angular/cdk/dialog';
import {ExpensesRevenueComponent} from './revenue-expenses/revenue-expenses.component';
import {NgxChartsModule} from '@swimlane/ngx-charts'
import {
    RevenueExpensesPerPeriodAndCategoryComponent
} from './revenue-expenses-per-period-and-category/revenue-expenses-per-period-and-category.component';
import {FiltersComponent} from './filters/filters.component';
import {ExpensesByCategoryComponent} from './uitgaven-per-categorie/expenses-by-category.component';
import {BankAccountSelectionComponent} from './bank-account-selection/bank-account-selection.component';
import {PeriodSelectionComponent} from './period-selection/period-selection.component';
import {TransactiontypeSelectionComponent} from './transactiontype-selection/transactiontype-selection.component';
import {GroupingTypeSelectionComponent} from './grouping-type-selection/grouping-type-selection.component';
import {RecurrenceComponent} from './recurrence/recurrence.component';
import {TransactionsComponent} from './transactions/transactions.component';
import {InsightsComponent} from './insights/insights.component';
import {NavigationComponent} from './navigation/navigation.component';
import {CategoryTreeDropdownComponent} from './category-tree-dropdown/category-tree-dropdown.component';

import {MatFormFieldModule} from "@angular/material/form-field";
import {BooleanRadioButtonGroupComponent} from './boolean-radio-button-group/boolean-radio-button-group.component';
import {TransactionSearchDialogComponent} from './transaction-search-dialog/transaction-search-dialog.component';
import {CounterpartyNameSelectionComponent} from './counterparty-name-selection/counterparty-name-selection.component';
import {NgSelectModule} from '@ng-select/ng-select';
import {
    CounterpartyAccountNumberSelectionComponent
} from './counterparty-account-number-selection/counterparty-account-number-selection.component';
import {
    TransactionCommunicationsSearchComponent
} from './transaction-mededelingen-search/transaction-communications-search.component';
import {DatePipe} from '@angular/common';
import {FileUploaderComponent} from './file-uploader/file-uploader.component';

import {LoginComponent} from './login/login.component';
import {AuthService} from "./auth/auth.service";
import {AuthGuard} from "./auth/auth.guard";
import {LoginLayoutComponent} from './layouts/login-layout/login-layout.component';
import {HomeLayoutComponent} from './layouts/home-layout/home-layout.component';
import {
    AnalysisForPeriodByCategoryComponent
} from './analysis-for-period-by-category/analysis-for-period-by-category.component';
import {ProfileComponent} from './profile/profile.component';
import {RegisterComponent} from './register/register.component';
import {ErrorDialogComponent} from './error-dialog/error-dialog.component';
import {CategorizationComponent} from './categorization/categorization.component';
import {BudgetComponent} from './budget/budget.component';
import {SaveErrorDialogComponent} from './budget/save-error-dialog/save-error-dialog.component';
import {RulesBuilderComponent} from './rules-builder/rules-builder.component';

import {FontAwesomeModule} from "@fortawesome/angular-fontawesome";

import {QueryBuilderComponent} from './query-builder/query-builder.component';
import {RulesViewComponent, RunCategorizationDialogComponent} from './rules-view/rules-view.component';
import {BankAccountCheckBoxesComponent} from './bank-account-check-boxes/bank-account-check-boxes.component';
import {IbanPipe} from './iban.pipe';
import {ManualCategorizationViewComponent} from './manual-categorization-view/manual-categorization-view.component';

import {ChartModule} from 'primeng/chart';
import {CategoryDetailsComponent} from './category-details/category-details.component';
import {ExpensesRevenueToggleComponent} from './expenses-revenue-toggle/expenses-revenue-toggle.component';
import {CriteriaToolbarComponent} from './criteria-toolbar/criteria-toolbar.component';
import {BudgetTrackingComponent} from './budget-tracking/budget-tracking.component';
import {TreeTableModule} from "primeng/treetable";
import {TransactionsInContextDialogComponent} from './transaction-dialog/transactions-in-context-dialog.component';
import {

    BASE_PATH,
    Configuration,

    ApiModule, ApiBudgetAssistantBackendClientService
} from '@daanvdn/budget-assistant-client';

import {AuthInterceptor} from "./auth.interceptor";
import {environment} from "../environments/environment";


@NgModule({ declarations: [
        AppComponent,
        ExpensesRevenueComponent,
        RevenueExpensesPerPeriodAndCategoryComponent,
        ExpensesByCategoryComponent,
        FiltersComponent,
        BankAccountSelectionComponent,
        PeriodSelectionComponent,
        TransactiontypeSelectionComponent,
        GroupingTypeSelectionComponent,
        RecurrenceComponent,
        TransactionsComponent,
        InsightsComponent,
        NavigationComponent,
        CategoryTreeDropdownComponent,
        BooleanRadioButtonGroupComponent,
        TransactionSearchDialogComponent,
        CounterpartyNameSelectionComponent,
        CounterpartyAccountNumberSelectionComponent,
        TransactionCommunicationsSearchComponent,
        FileUploaderComponent,
        LoginComponent,
        LoginLayoutComponent,
        HomeLayoutComponent,
        AnalysisForPeriodByCategoryComponent,
        ProfileComponent,
        RegisterComponent,
        ErrorDialogComponent,
        CategorizationComponent,
        BudgetComponent,
        SaveErrorDialogComponent,
        RulesBuilderComponent,
        QueryBuilderComponent,
        RulesViewComponent,
        RunCategorizationDialogComponent,
        BankAccountCheckBoxesComponent,
        IbanPipe,
        ManualCategorizationViewComponent,
        CategoryDetailsComponent,
        ExpensesRevenueToggleComponent,
        CriteriaToolbarComponent,
        BudgetTrackingComponent,
        TransactionsInContextDialogComponent,
    ],
    exports: [
        NgSelectModule,
        NgxChartsModule,
        A11yModule,
        CdkAccordionModule,
        ClipboardModule,
        CdkMenuModule,
        CdkStepperModule,
        CdkTableModule,
        CdkTreeModule,
        DragDropModule,
        MatAutocompleteModule,
        MatBadgeModule,
        MatBottomSheetModule,
        MatButtonModule,
        MatButtonToggleModule,
        MatCardModule,
        MatCheckboxModule,
        MatChipsModule,
        MatStepperModule,
        MatDatepickerModule,
        MatDialogModule,
        MatDividerModule,
        MatExpansionModule,
        MatGridListModule,
        MatIconModule,
        MatInputModule,
        MatListModule,
        MatMenuModule,
        MatNativeDateModule,
        MatPaginatorModule,
        MatProgressBarModule,
        MatProgressSpinnerModule,
        MatRadioModule,
        MatRippleModule,
        MatSelectModule,
        MatSidenavModule,
        MatSliderModule,
        MatSlideToggleModule,
        MatSnackBarModule,
        MatSortModule,
        MatTableModule,
        MatTabsModule,
        MatToolbarModule,
        MatTooltipModule,
        MatTreeModule,
        OverlayModule,
        PortalModule,
        ScrollingModule,
        DialogModule,
        MatCardModule,
        InsightsComponent,
        TransactionsComponent,
        TransactiontypeSelectionComponent,
        QueryBuilderComponent,
        MatTabsModule,
    ],
    bootstrap: [AppComponent], imports: [CdkMenuModule,
        NgSelectModule,
        BrowserAnimationsModule,
        MatTooltipModule,
        MatSortModule,
        MatTreeModule,
        MatAutocompleteModule,
        MatFormFieldModule,
        NgxChartsModule,
        BrowserModule,
        AppRoutingModule,
        BrowserAnimationsModule,
        FormsModule,
        MatNativeDateModule,
        ReactiveFormsModule,
        MatToolbarModule,
        MatButtonModule,
        MatDialogModule,
        MatInputModule,
        MatSelectModule,
        MatTableModule,
        MatSortModule,
        MatPaginatorModule,
        MatNativeDateModule,
        MatDatepickerModule,
        MatCardModule,
        MatCheckboxModule,
        MatRadioModule,
        MatSidenavModule,
        MatListModule,
        MatIconModule,
        MatGridListModule,
        MatProgressSpinnerModule,
        FontAwesomeModule,
        MatTabsModule,
        MatButtonToggleModule,
        MatExpansionModule,
        MatBadgeModule,
        ChartModule,
        TreeTableModule,
        ApiModule.forRoot(() => {
            return new Configuration({
                basePath: environment.API_BASE_PATH,
            });
        })], providers: [
        ApiBudgetAssistantBackendClientService,
        AuthService, AuthGuard,
        DatePipe,
        { provide: HTTP_INTERCEPTORS, useClass: AuthInterceptor, multi: true },
        {
            provide: Configuration,
            useFactory: () => new Configuration(),
        },
        { provide: BASE_PATH, useValue: environment.API_BASE_PATH },
        provideHttpClient(withInterceptorsFromDi())
    ] })
export class AppModule {
}
