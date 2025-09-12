import { formatDate, NgIf, NgFor } from '@angular/common';
import {
  Component,
  effect,
  EventEmitter,
  OnChanges,
  OnInit,
  Output,
  signal,
  ViewChild,
  WritableSignal
} from '@angular/core';
import { FormBuilder, FormControl, FormGroup, FormsModule, ReactiveFormsModule } from '@angular/forms';
import {
  DateAdapter,
  MAT_DATE_FORMATS,
  NativeDateAdapter,
  MatOption,
  provideNativeDateAdapter
} from '@angular/material/core';
import {NgSelectComponent} from '@ng-select/ng-select';
import {AppService} from '../app.service';
import {ResolvedStartEndDateShortcut, StartEndDateShortcut} from '../model';
import { DateFilterFn, MatDateRangeInput, MatStartDate, MatEndDate, MatDatepickerToggle, MatDateRangePicker } from "@angular/material/datepicker";
import { MatFormField, MatLabel, MatSuffix } from '@angular/material/form-field';
import { MatButton } from '@angular/material/button';
import { MatSelect } from '@angular/material/select';
import {CreateQueryResult, injectQuery, keepPreviousData} from "@tanstack/angular-query-experimental";
import {firstValueFrom} from "rxjs";

export const PICK_FORMATS = {
  parse: { dateInput: { month: 'short', year: 'numeric', day: 'numeric' } },
  display: {
    dateInput: 'input',
    monthYearLabel: { year: 'numeric', month: 'short' },
    dateA11yLabel: { year: 'numeric', month: 'long', day: 'numeric' },
    monthYearA11yLabel: { year: 'numeric', month: 'long' }
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
    selector: 'period-selection',
    templateUrl: './period-selection.component.html',
    styleUrls: ['./period-selection.component.scss'],
    providers: [
        { provide: DateAdapter, useClass: PickDateAdapter },
        { provide: MAT_DATE_FORMATS, useValue: PICK_FORMATS }
    ],
    standalone: true,
    imports: [MatFormField, MatLabel, MatDateRangeInput, FormsModule, ReactiveFormsModule, MatStartDate, MatEndDate, MatDatepickerToggle, MatSuffix, MatDateRangePicker, NgIf, MatButton, MatSelect, NgFor, MatOption]
})
export class PeriodSelectionComponent implements OnInit, OnChanges {

  formFieldGroup: FormGroup;
  startDate: any;
  endDate: any;
  selectedShortcut: WritableSignal<StartEndDateShortcut> = signal<StartEndDateShortcut>(StartEndDateShortcut.ALL);


  startEndDateShortCuts: Map<string, StartEndDateShortcut> = new Map<string, StartEndDateShortcut>();
  startEndDateShortCutStringValues: string[];

  range = new FormGroup({
    start: new FormControl<Date | null>(null),
    end: new FormControl<Date | null>(null),
  });

  @Output() change: EventEmitter<Date[]> = new EventEmitter<Date[]>(true);

  displayShortcutsAsDropdown: boolean = true;
  periodShortcutDropDownSelection!: string;
  public resolvedPeriodShortcutQuery: CreateQueryResult<ResolvedStartEndDateShortcut, Error>;


  allowDate: DateFilterFn<any> = function (date: Date | null): boolean {
    if (!date) {
      return false;
    }
    //check if date is first day of month or last day of month
    return date.getDate() === 1 || new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate() === date.getDate();



  };

  constructor(private appService: AppService, private formBuilder: FormBuilder) {
      this.formFieldGroup = formBuilder.group({ queryForm: "" });

    this.startEndDateShortCuts.set("huidige maand", StartEndDateShortcut.CURRENT_MONTH);
    this.startEndDateShortCuts.set("vorige maand", StartEndDateShortcut.PREVIOUS_MONTH);
    this.startEndDateShortCuts.set("huidig kwartaal", StartEndDateShortcut.CURRENT_QUARTER);
    this.startEndDateShortCuts.set("vorig kwartaal", StartEndDateShortcut.PREVIOUS_QUARTER);
    this.startEndDateShortCuts.set("huidig jaar", StartEndDateShortcut.CURRENT_YEAR);
    this.startEndDateShortCuts.set("vorig jaar", StartEndDateShortcut.PREVIOUS_YEAR);
    this.startEndDateShortCuts.set("alles", StartEndDateShortcut.ALL);
    this.startEndDateShortCutStringValues = Array.from(this.startEndDateShortCuts.keys());
    this.resolvedPeriodShortcutQuery = injectQuery(() => ({
      queryKey: ['resolvedPeriodShortcut', this.selectedShortcut()],
      queryFn: () => firstValueFrom(this.appService.resolveStartEndDateShortcut(this.selectedShortcut())),
      staleTime: 5 * 60 * 1000, // 5 minutes,
      placeholderData: keepPreviousData
    }));

    effect(() => {

      const resolvedShortCut: ResolvedStartEndDateShortcut | undefined = this.resolvedPeriodShortcutQuery.data();
      if (resolvedShortCut ) {
        this.range.controls.start.setValue(new Date(resolvedShortCut.start));
        this.range.controls.end.setValue(new Date(resolvedShortCut.end));
        this.startDate = resolvedShortCut.start;
        this.endDate = resolvedShortCut.end;
        this.change.emit([this.startDate, this.endDate]);
        this.appService.setStartAndEndDate(this.startDate, this.endDate);



      }
    }, {allowSignalWrites: true});
  }



  ngOnInit() {



  }

  getDropdownKeys(): string[] {
    return Array.from(this.startEndDateShortCuts.keys())
  }

  ngOnChanges() {
    let startDate = new Date(this.startDate);
    let endDate = new Date(this.endDate);
    this.change.emit([startDate, endDate]);
    this.appService.setStartAndEndDate(startDate, endDate);
  }



  onPeriodShortCutClick(periodStr: string) {
    let value = this.startEndDateShortCuts.get(periodStr);
    if( value === undefined) {
      value = StartEndDateShortcut.ALL;
    }
    this.selectedShortcut.set(value);


  }


  /**
   * we cannot use two-way binding on ngModel because of how ng-select works. so this is a workaround
   * @returns
   */
  onDropDownChange() {
    if (this.periodShortcutDropDownSelection === null || this.periodShortcutDropDownSelection === undefined) {
        return;
    }

    var shortCut: StartEndDateShortcut | undefined = this.startEndDateShortCuts.get(this.periodShortcutDropDownSelection);
    if (shortCut == undefined) {
      shortCut = StartEndDateShortcut.ALL;
    }
    this.selectedShortcut.set(shortCut);

  }



}
