import {Component, Inject, OnInit, OnDestroy, signal} from '@angular/core';
import {
    MatDialogRef,
    MAT_DIALOG_DATA,
    MatDialogTitle,
    MatDialogContent,
    MatDialogActions
} from '@angular/material/dialog';
import {FormControl, FormGroup, FormsModule, ReactiveFormsModule} from '@angular/forms';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatInputModule} from '@angular/material/input';
import {MatSelectModule} from '@angular/material/select';
import {MatAutocompleteModule} from '@angular/material/autocomplete';
import {MatDatepickerModule} from '@angular/material/datepicker';
import {MatButtonModule} from '@angular/material/button';
import {MatIconModule} from '@angular/material/icon';
import {AsyncPipe, CommonModule} from '@angular/common';
import {DateAdapter, MAT_DATE_FORMATS, NativeDateAdapter, MatNativeDateModule} from '@angular/material/core';
import {Observable, Subject, map, startWith} from 'rxjs';
import {takeUntil} from 'rxjs/operators';
import {formatDate} from '@angular/common';

import {CategoryTreeDropdownComponent} from '../category-tree-dropdown/category-tree-dropdown.component';
import {AppService} from '../app.service';
import {StartEndDateShortcut} from '../model';
import {AmountType} from '../model';
import {
    CategoryIndex,
    TransactionQuery,
    TransactionTypeEnum,
    BankAccountRead
} from '@daanvdn/budget-assistant-client';

// Custom date format
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

interface TransactionTypeOption {
    label: string;
    value: TransactionTypeEnum;
}

interface PeriodShortcutOption {
    label: string;
    value: StartEndDateShortcut;
}

@Component({
    selector: 'app-transaction-search-dialog',
    templateUrl: './transaction-search-dialog.component.html',
    styleUrls: ['./transaction-search-dialog.component.scss'],
    standalone: true,
    providers: [
        {provide: DateAdapter, useClass: PickDateAdapter},
        {provide: MAT_DATE_FORMATS, useValue: PICK_FORMATS}
    ],
    imports: [
        CommonModule,
        FormsModule,
        ReactiveFormsModule,
        MatDialogTitle,
        MatDialogContent,
        MatDialogActions,
        MatFormFieldModule,
        MatInputModule,
        MatSelectModule,
        MatAutocompleteModule,
        MatDatepickerModule,
        MatButtonModule,
        MatIconModule,
        MatNativeDateModule,
        AsyncPipe,
        CategoryTreeDropdownComponent
    ]
})
export class TransactionSearchDialogComponent implements OnInit, OnDestroy {
    private destroy$ = new Subject<void>();

    // Category index for lookup
    private categoryIndex?: CategoryIndex;

    // Transaction Type options
    transactionTypeOptions: TransactionTypeOption[] = [
        {label: 'in- & uitkomsten', value: TransactionTypeEnum.BOTH},
        {label: 'uitgaven', value: TransactionTypeEnum.EXPENSES},
        {label: 'inkomsten', value: TransactionTypeEnum.REVENUE}
    ];

    // Period shortcut options
    periodShortcutOptions: PeriodShortcutOption[] = [
        {label: 'huidige maand', value: StartEndDateShortcut.CURRENT_MONTH},
        {label: 'vorige maand', value: StartEndDateShortcut.PREVIOUS_MONTH},
        {label: 'huidig kwartaal', value: StartEndDateShortcut.CURRENT_QUARTER},
        {label: 'vorig kwartaal', value: StartEndDateShortcut.PREVIOUS_QUARTER},
        {label: 'huidig jaar', value: StartEndDateShortcut.CURRENT_YEAR},
        {label: 'vorig jaar', value: StartEndDateShortcut.PREVIOUS_YEAR},
        {label: 'alles', value: StartEndDateShortcut.ALL}
    ];

    // Form controls
    transactionTypeControl = new FormControl<TransactionTypeEnum | null>(null);
    minAmountControl = new FormControl<number | null>(null);
    maxAmountControl = new FormControl<number | null>(null);
    periodShortcutControl = new FormControl<StartEndDateShortcut | null>(null);
    counterpartyNameControl = new FormControl<string>('');
    counterpartyAccountControl = new FormControl<string>('');
    communicationTextControl = new FormControl<string>('');

    // Date range form group
    range = new FormGroup({
        start: new FormControl<Date | null>(null),
        end: new FormControl<Date | null>(null)
    });

    // Signal for selected category
    selectedCategoryId = signal<number | undefined>(undefined);

    // Validation state
    showValidationError = false;

    // Autocomplete data
    counterpartyNames: string[] = [];
    counterpartyAccounts: string[] = [];
    filteredCounterpartyNames$!: Observable<string[]>;
    filteredCounterpartyAccounts$!: Observable<string[]>;

    protected readonly AmountType = AmountType;

    constructor(
        public dialogRef: MatDialogRef<TransactionSearchDialogComponent>,
        @Inject(MAT_DIALOG_DATA) public data: TransactionQuery,
        private appService: AppService
    ) {
        // Subscribe to category index
        this.appService.categoryIndexObservable$
            .pipe(takeUntil(this.destroy$))
            .subscribe((categoryIndex: CategoryIndex | undefined) => {
                this.categoryIndex = categoryIndex;
            });
    }

    ngOnInit(): void {
        // Load counterparty names and accounts from backend
        this.appService.selectedBankAccountObservable$
            .pipe(takeUntil(this.destroy$))
            .subscribe((bankAccount: BankAccountRead | undefined) => {
                if (bankAccount) {
                    // Load counterparty names
                    this.appService.getDistinctCounterpartyNames(bankAccount.accountNumber)
                        .pipe(takeUntil(this.destroy$))
                        .subscribe(names => {
                            this.counterpartyNames = names;
                            this.setupCounterpartyNameFilter();
                        });

                    // Load counterparty accounts
                    this.appService.getDistinctCounterpartyAccounts(bankAccount.accountNumber)
                        .pipe(takeUntil(this.destroy$))
                        .subscribe(accounts => {
                            this.counterpartyAccounts = accounts;
                            this.setupCounterpartyAccountFilter();
                        });
                }
            });

        // Setup period shortcut subscription
        this.periodShortcutControl.valueChanges
            .pipe(takeUntil(this.destroy$))
            .subscribe(shortcut => {
                if (shortcut) {
                    this.onPeriodShortcutChange(shortcut);
                }
            });
    }

    ngOnDestroy(): void {
        this.destroy$.next();
        this.destroy$.complete();
    }

    private setupCounterpartyNameFilter(): void {
        this.filteredCounterpartyNames$ = this.counterpartyNameControl.valueChanges.pipe(
            startWith(''),
            map(value => this.filterOptions(value || '', this.counterpartyNames))
        );
    }

    private setupCounterpartyAccountFilter(): void {
        this.filteredCounterpartyAccounts$ = this.counterpartyAccountControl.valueChanges.pipe(
            startWith(''),
            map(value => this.filterOptions(value || '', this.counterpartyAccounts))
        );
    }

    private filterOptions(value: string, options: string[]): string[] {
        const filterValue = value.toLowerCase();
        return options.filter(option => option.toLowerCase().includes(filterValue));
    }

    onPeriodShortcutChange(shortcut: StartEndDateShortcut): void {
        this.appService.resolveStartEndDateShortcut(shortcut)
            .pipe(takeUntil(this.destroy$))
            .subscribe(resolved => {
                // Parse dates - handle the resolved dates properly
                // const startDate = this.parseAndValidateDate(resolved.start);
                // const endDate = this.parseAndValidateDate(resolved.end);
                const startDate = resolved.start;
                const endDate = resolved.end;

                this.range.controls.start.setValue(startDate);
                this.range.controls.end.setValue(endDate);
            });
    }

    /**
     * Parse and validate date to avoid invalid dates (year 0001, 0005, etc.)
     */
    private parseAndValidateDate(dateValue: Date | string | null | undefined): Date | null {
        if (!dateValue) {
            return null;
        }

        let date: Date;

        if (dateValue instanceof Date) {
            date = dateValue;
        } else if (typeof dateValue === 'string') {
            // Try parsing YYYY-MM-DD format
            if (/^\d{4}-\d{2}-\d{2}$/.test(dateValue)) {
                const [year, month, day] = dateValue.split('-').map(Number);
                date = new Date(year, month - 1, day);
            } else {
                date = new Date(dateValue);
            }
        } else {
            return null;
        }

        // Validate the date - reject years before 1900 or invalid dates
        if (isNaN(date.getTime()) || date.getFullYear() < 1900 || date.getFullYear() > 2100) {
            return null;
        }

        return date;
    }

    handleCategorySelectionChange(categoryQualifiedName: string | undefined): void {
        if (!categoryQualifiedName || !this.categoryIndex) {
            this.selectedCategoryId.set(undefined);
            return;
        }

        const categoryId = this.categoryIndex.qualifiedNameToIdIndex[categoryQualifiedName];
        this.selectedCategoryId.set(categoryId);
    }

    onCancelClick(): void {
        this.dialogRef.close();
    }

    onSearchClick(): void {
        if (!this.hasAnyFilter()) {
            this.showValidationError = true;
            return;
        }
        this.showValidationError = false;
        const query = this.buildTransactionQuery();
        this.dialogRef.close(query);
    }

    /**
     * Check if at least one filter is specified
     */
    hasAnyFilter(): boolean {
        const hasTransactionType = this.transactionTypeControl.value !== null;
        const hasMinAmount = this.minAmountControl.value !== null && this.minAmountControl.value !== undefined;
        const hasMaxAmount = this.maxAmountControl.value !== null && this.maxAmountControl.value !== undefined;
        const hasStartDate = this.range.controls.start.value !== null;
        const hasEndDate = this.range.controls.end.value !== null;
        const hasCounterpartyName = !!this.counterpartyNameControl.value?.trim();
        const hasCounterpartyAccount = !!this.counterpartyAccountControl.value?.trim();
        const hasCommunicationText = !!this.communicationTextControl.value?.trim();
        const hasCategory = this.selectedCategoryId() !== undefined;

        return hasTransactionType || hasMinAmount || hasMaxAmount ||
               hasStartDate || hasEndDate || hasCounterpartyName ||
               hasCounterpartyAccount || hasCommunicationText || hasCategory;
    }

    private dateToString(date: Date | null): string | undefined {
        if (!date) {
            return undefined;
        }
        return date.toISOString().split('T')[0];
    }

    private buildTransactionQuery(): TransactionQuery {
        const startDate = this.range.controls.start.value;
        const endDate = this.range.controls.end.value;

        const query: TransactionQuery = {
            transactionType: this.transactionTypeControl.value ?? undefined,
            minAmount: this.minAmountControl.value ?? undefined,
            maxAmount: this.maxAmountControl.value ?? undefined,
            startDate: this.dateToString(startDate),
            endDate: this.dateToString(endDate),
            counterpartyName: this.counterpartyNameControl.value || undefined,
            counterpartyAccountNumber: this.counterpartyAccountControl.value || undefined,
            transactionOrCommunication: this.communicationTextControl.value || undefined,
            categoryId: this.selectedCategoryId(),
            accountNumber: undefined, // Will be set by the parent component
            uploadTimestamp: undefined,
            manuallyAssignedCategory: undefined
        };

        return query;
    }

    // Computed property for the transaction type to pass to category dropdown
    get transactionTypeForCategory(): TransactionTypeEnum {
        return this.transactionTypeControl.value ?? TransactionTypeEnum.BOTH;
    }
}
