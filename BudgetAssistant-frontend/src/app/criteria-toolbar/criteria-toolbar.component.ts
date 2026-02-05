import {Component, EventEmitter, Input, OnDestroy, OnInit, Output, signal} from '@angular/core';
import {NgIf} from '@angular/common';
import {FormControl, FormGroup, FormsModule, ReactiveFormsModule} from '@angular/forms';
import {Subject, takeUntil} from 'rxjs';

import {MatButtonToggleChange, MatButtonToggleGroup, MatButtonToggle} from '@angular/material/button-toggle';
import {MatIconButton} from '@angular/material/button';
import {MatIconModule} from '@angular/material/icon';
import {MatTooltipModule} from '@angular/material/tooltip';
import {MatSelectModule} from '@angular/material/select';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatDatepickerModule} from '@angular/material/datepicker';
import {DateAdapter, MAT_DATE_FORMATS, NativeDateAdapter} from '@angular/material/core';
import {formatDate} from '@angular/common';

import {BankAccountRead, Grouping, TransactionTypeEnum} from '@daanvdn/budget-assistant-client';
import {BankAccountSelectionComponent} from '../bank-account-selection/bank-account-selection.component';
import {Criteria} from '../model/criteria.model';
import {anyIsUndefinedOrEmpty, StartEndDateShortcut} from '../model';
import {AppService} from '../app.service';

// Custom date adapter for date picker formatting
export const PICK_FORMATS = {
    parse: {dateInput: {month: 'short', year: 'numeric', day: 'numeric'}},
    display: {
        dateInput: 'input',
        monthYearLabel: {year: 'numeric', month: 'short'},
        dateA11yLabel: {year: 'numeric', month: 'long', day: 'numeric'},
        monthYearA11yLabel: {year: 'numeric', month: 'long'}
    }
};

class PickDateAdapter extends NativeDateAdapter {
    override format(date: Date, displayFormat: Object): string {
        if (displayFormat === 'input') {
            return formatDate(date, 'dd-MMM-yyyy', this.locale);
        } else {
            return date.toDateString();
        }
    }
}

// Period shortcut interface for chip selection
interface PeriodShortcut {
    label: string;
    value: StartEndDateShortcut;
    icon: string;
}

@Component({
    selector: 'criteria-toolbar',
    templateUrl: './criteria-toolbar.component.html',
    styleUrls: ['./criteria-toolbar.component.scss'],
    standalone: true,
    providers: [
        {provide: DateAdapter, useClass: PickDateAdapter},
        {provide: MAT_DATE_FORMATS, useValue: PICK_FORMATS}
    ],
    imports: [
        NgIf,
        FormsModule,
        ReactiveFormsModule,
        BankAccountSelectionComponent,
        MatButtonToggleGroup,
        MatButtonToggle,
        MatIconButton,
        MatIconModule,
        MatTooltipModule,
        MatSelectModule,
        MatFormFieldModule,
        MatDatepickerModule
    ]
})
export class CriteriaToolbarComponent implements OnInit, OnDestroy {
    // Input flags to enable/disable sections
    @Input() enableBankAccountSelection = true;
    @Input() enableGroupingTypeSelection = true;
    @Input() enablePeriodSelection = true;
    @Input() enableExpensesRevenueToggle = true;
    @Input() enableCloseButton = true;

    // Output events
    @Output() closed = new EventEmitter<boolean>();
    @Output() criteriaChange = new EventEmitter<Criteria>();

    // Current state using signals for reactivity
    bankAccount = signal<BankAccountRead | undefined>(undefined);
    grouping = signal<Grouping>(Grouping.MONTH);
    startDate = signal<Date | undefined>(undefined);
    endDate = signal<Date | undefined>(undefined);
    transactionType = signal<TransactionTypeEnum>(TransactionTypeEnum.EXPENSES);

    // Current criteria for comparison
    private currentCriteria: Criteria | undefined;
    private destroy$ = new Subject<void>();

    // Grouping options for the toggle group
    readonly groupingOptions: {value: Grouping; icon: string; tooltip: string}[] = [
        {value: Grouping.MONTH, icon: 'calendar_view_month', tooltip: 'Month'},
        {value: Grouping.QUARTER, icon: 'calendar_today', tooltip: 'Quarter'},
        {value: Grouping.YEAR, icon: 'calendar_month', tooltip: 'Year'}
    ];

    // Period shortcuts for chip selection
    readonly periodShortcuts: PeriodShortcut[] = [
        {label: 'This Month', value: StartEndDateShortcut.CURRENT_MONTH, icon: 'today'},
        {label: 'Last Month', value: StartEndDateShortcut.PREVIOUS_MONTH, icon: 'event'},
        {label: 'This Quarter', value: StartEndDateShortcut.CURRENT_QUARTER, icon: 'date_range'},
        {label: 'Last Quarter', value: StartEndDateShortcut.PREVIOUS_QUARTER, icon: 'date_range'},
        {label: 'This Year', value: StartEndDateShortcut.CURRENT_YEAR, icon: 'calendar_month'},
        {label: 'Last Year', value: StartEndDateShortcut.PREVIOUS_YEAR, icon: 'calendar_month'},
        {label: 'All Time', value: StartEndDateShortcut.ALL, icon: 'all_inclusive'}
    ];

    // Selected period shortcut
    selectedPeriodShortcut = signal<StartEndDateShortcut | undefined>(undefined);

    // Date range form group
    dateRange = new FormGroup({
        start: new FormControl<Date | null>(null),
        end: new FormControl<Date | null>(null)
    });

    // Date filter function - only allow first/last day of month
    dateFilter = (date: Date | null): boolean => {
        if (!date) return false;
        const day = date.getDate();
        const lastDayOfMonth = new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
        return day === 1 || day === lastDayOfMonth;
    };

    constructor(private appService: AppService) {}

    ngOnInit(): void {
        // Initialize with default values
        this.appService.setGrouping(this.grouping());
        this.appService.setTransactionType(this.transactionType());

        // Initialize period with "All" shortcut
        this.onPeriodShortcutSelect(StartEndDateShortcut.ALL);
    }

    ngOnDestroy(): void {
        this.destroy$.next();
        this.destroy$.complete();
    }

    // Bank account change handler
    onBankAccountChange(bankAccount: BankAccountRead): void {
        this.bankAccount.set(bankAccount);
        this.maybeEmitCriteriaChange();
    }

    // Grouping type change handler
    onGroupingChange(groupingValue: Grouping): void {
        this.grouping.set(groupingValue);
        this.appService.setGrouping(groupingValue);
        this.maybeEmitCriteriaChange();
    }

    // Period shortcut selection handler
    onPeriodShortcutSelect(shortcut: StartEndDateShortcut): void {
        this.selectedPeriodShortcut.set(shortcut);

        this.appService.resolveStartEndDateShortcut(shortcut)
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: (resolved) => {
                    const start = new Date(resolved.start);
                    const end = new Date(resolved.end);

                    this.startDate.set(start);
                    this.endDate.set(end);
                    this.dateRange.controls.start.setValue(start);
                    this.dateRange.controls.end.setValue(end);

                    this.appService.setStartAndEndDate(start, end);
                    this.maybeEmitCriteriaChange();
                },
                error: (err) => console.error('Error resolving date shortcut:', err)
            });
    }

    // Manual date change handler
    onDateRangeChange(): void {
        const start = this.dateRange.controls.start.value;
        const end = this.dateRange.controls.end.value;

        if (start && end) {
            this.startDate.set(start);
            this.endDate.set(end);
            this.selectedPeriodShortcut.set(undefined); // Clear shortcut selection
            this.appService.setStartAndEndDate(start, end);
            this.maybeEmitCriteriaChange();
        }
    }

    // Transaction type toggle handler
    onTransactionTypeChange(event: MatButtonToggleChange): void {
        const value = event.value as 'expenses' | 'revenue';
        const transactionType = value === 'expenses' 
            ? TransactionTypeEnum.EXPENSES 
            : TransactionTypeEnum.REVENUE;

        this.transactionType.set(transactionType);
        this.appService.setTransactionType(transactionType);
        this.maybeEmitCriteriaChange();
    }

    // Close button handler
    onClickClose(): void {
        this.closed.emit(true);
    }

    // Check if all required fields are set
    private requiredFieldsAreSet(): boolean {
        if (this.enableExpensesRevenueToggle && !this.transactionType()) {
            return false;
        }
        if (this.enableBankAccountSelection && !this.bankAccount()) {
            return false;
        }
        if (this.enableGroupingTypeSelection && !this.grouping()) {
            return false;
        }
        if (this.enablePeriodSelection && anyIsUndefinedOrEmpty(this.startDate(), this.endDate())) {
            return false;
        }
        return true;
    }

    // Emit criteria change if all required fields are set
    private maybeEmitCriteriaChange(): void {
        if (!this.requiredFieldsAreSet()) {
            return;
        }

        const bankAccount = this.bankAccount();
        const startDate = this.startDate();
        const endDate = this.endDate();

        if (!bankAccount || !startDate || !endDate) {
            return;
        }

        const criteria = new Criteria(
            bankAccount,
            this.grouping(),
            startDate,
            endDate,
            this.transactionType()
        );

        if (!this.currentCriteria || !this.currentCriteria.equals(criteria)) {
            this.currentCriteria = criteria;
            this.criteriaChange.emit(criteria);
        }
    }
}
