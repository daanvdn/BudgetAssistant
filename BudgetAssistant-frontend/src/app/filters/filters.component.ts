import {Component, OnInit} from '@angular/core';
import { FormBuilder, FormControl, FormGroup, FormsModule, ReactiveFormsModule } from '@angular/forms';
import {AppService} from '../app.service';
import {StartEndDateShortcut} from '../model';

import { DateAdapter, MAT_DATE_FORMATS, NativeDateAdapter, MatOption } from '@angular/material/core';
import { formatDate, NgFor } from '@angular/common';
import {Subject, takeUntil} from "rxjs";
import {BankAccountRead, Grouping, TransactionTypeEnum} from "@daanvdn/budget-assistant-client";
import { MatFormField, MatLabel, MatHint, MatSuffix } from '@angular/material/form-field';
import { MatSelect } from '@angular/material/select';
import { MatDateRangeInput, MatStartDate, MatEndDate, MatDatepickerToggle, MatDateRangePicker } from '@angular/material/datepicker';
import { MatButton } from '@angular/material/button';

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

@Component({
    selector: 'app-filters',
    templateUrl: './filters.component.html',
    styleUrls: ['./filters.component.scss'],
    providers: [
        { provide: DateAdapter, useClass: PickDateAdapter },
        { provide: MAT_DATE_FORMATS, useValue: PICK_FORMATS }
    ],
    standalone: true,
    imports: [FormsModule, ReactiveFormsModule, MatFormField, MatLabel, MatSelect, NgFor, MatOption, MatDateRangeInput, MatStartDate, MatEndDate, MatHint, MatDatepickerToggle, MatSuffix, MatDateRangePicker, MatButton]
})
export class FiltersComponent implements OnInit {


  bankAccountFormFieldGroup: FormGroup;


  bankAccounts: BankAccountRead[] = [];

  startEndDateFormFieldGroup: FormGroup;

  groupingTypesFormFieldGroup: FormGroup;

  groupingTypes: Map<string, Grouping> = new Map<string, Grouping>();
  groupingTypeStringValues: string[];


  transactionTypeFormFieldGroup: FormGroup;
  transactionTypes: Map<string, TransactionTypeEnum> = new Map<string, TransactionTypeEnum>();
  transactionTypeStringValues: string[];

  startEndDateShortCuts: Map<string, StartEndDateShortcut> = new Map<string, StartEndDateShortcut>();
  startEndDateShortCutStringValues: string[];


  startDate = new FormControl<Date | null>(null);
  endDate = new FormControl<Date | null>(null);
  private destroy$ = new Subject<void>();

  constructor(private appService: AppService, private formBuilder: FormBuilder) {
    this.appService.fetchBankAccountsForUser()
      .pipe(takeUntil(this.destroy$))

      .subscribe(result => {
          if (result == undefined) {
            return;
          }
          this.appService.setBankAccount(result[0]);
          return this.bankAccounts = result
        }
      )
    this.bankAccountFormFieldGroup = formBuilder.group({queryForm: ""});
    this.startEndDateFormFieldGroup = formBuilder.group({queryForm: ""});
    this.transactionTypeFormFieldGroup = formBuilder.group({queryForm: ""});
    this.transactionTypeFormFieldGroup = formBuilder.group({queryForm: ""});
    this.groupingTypesFormFieldGroup = formBuilder.group({queryForm: ""});

    this.groupingTypes.set("month", Grouping.MONTH)
    this.groupingTypes.set("year", Grouping.YEAR)
    this.groupingTypes.set("quarter", Grouping.QUARTER)
    this.groupingTypeStringValues = Array.from(this.groupingTypes.keys());


    this.startEndDateShortCuts.set("huidige maand", StartEndDateShortcut.CURRENT_MONTH);
    this.startEndDateShortCuts.set("huidig kwartaal", StartEndDateShortcut.CURRENT_QUARTER);
    this.startEndDateShortCuts.set("huidig jaar", StartEndDateShortcut.CURRENT_YEAR);
    this.startEndDateShortCuts.set("alles", StartEndDateShortcut.ALL);
    this.startEndDateShortCutStringValues = Array.from(this.startEndDateShortCuts.keys());


    this.transactionTypes.set("in- & uitkomsten", TransactionTypeEnum.BOTH)
    this.transactionTypes.set("uitgaven", TransactionTypeEnum.EXPENSES)
    this.transactionTypes.set("inkomsten", TransactionTypeEnum.REVENUE)
    this.transactionTypeStringValues = Array.from(this.transactionTypes.keys());


  }

  ngOnInit() {
  }

  dateClass = (d: Date) => {
    const date = d.getDay();
    // Highlight saturday and sunday.
    return (date === 0 || date === 6) ? 'highlight-dates' : undefined;
  }

  onBankAccountChange(bankAccount: BankAccountRead) {
    this.appService.setBankAccount(bankAccount);


  }


  setStartAndEndDate() {
    console.log(this.startDate.value);
    console.log(this.endDate.value);
    if (this.startDate.value && this.endDate.value) {

      this.appService.setStartAndEndDate(this.startDate.value, this.endDate.value)
    }
  }

  onTransactionTypeChange(transactionTypeStr: string) {
    console.log(transactionTypeStr);
    var transactionType: TransactionTypeEnum | undefined = this.transactionTypes.get(transactionTypeStr)
    if (transactionType == undefined) {
      transactionType = TransactionTypeEnum.BOTH;
    }
    this.appService.setTransactionType(transactionType);
  }

  onGroupingChange(groupingStr: string) {
    console.log(groupingStr);
    var groupingType: Grouping | undefined = this.groupingTypes.get(groupingStr)
    if (groupingType == undefined) {
      groupingType = Grouping.MONTH;
    }
    this.appService.setGrouping(groupingType);
  }

  onPeriodShortCutClick(periodStr: string) {
    var shortCut: StartEndDateShortcut | undefined = this.startEndDateShortCuts.get(periodStr);


    if (shortCut == undefined) {
      shortCut = StartEndDateShortcut.ALL;
    }

    this.appService.resolveStartEndDateShortcut(shortCut).subscribe(resolved => {

      this.startDate.setValue(resolved.start);
      this.endDate.setValue(resolved.end);
    })

  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }


}
