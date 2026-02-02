import {Component, EventEmitter, OnInit, Output} from '@angular/core';
import { FormBuilder, FormGroup, FormsModule, ReactiveFormsModule } from '@angular/forms';
import {AppService} from '../app.service';
import {Grouping} from "@daanvdn/budget-assistant-client";
import { MatFormField, MatLabel } from '@angular/material/form-field';
import { MatSelect } from '@angular/material/select';
import { NgFor } from '@angular/common';
import { MatOption } from '@angular/material/core';

@Component({
    selector: 'grouping-type-selection',
    templateUrl: './grouping-type-selection.component.html',
    styleUrls: ['./grouping-type-selection.component.scss'],
    standalone: true,
    imports: [FormsModule, ReactiveFormsModule, MatFormField, MatLabel, MatSelect, NgFor, MatOption]
})
export class GroupingTypeSelectionComponent implements OnInit {

  groupingTypesFormFieldGroup: FormGroup;

  groupingTypes: Map<string, Grouping> = new Map<string, Grouping>();
  groupingTypeStringValues: string[];
  selectedGrouping!: Grouping;
  @Output() change: EventEmitter<Grouping> = new EventEmitter<Grouping>(true);



  constructor(formBuilder: FormBuilder, private appService: AppService) {

    this.groupingTypesFormFieldGroup = formBuilder.group({ queryForm: "" });
    this.groupingTypes.set("month", Grouping.MONTH)
    this.groupingTypes.set("year", Grouping.YEAR)
    this.groupingTypes.set("quarter", Grouping.QUARTER)
    this.groupingTypeStringValues = Array.from(this.groupingTypes.keys());
    this.selectedGrouping = Grouping.MONTH;

  }

  ngOnInit() {
    this.change.emit(this.selectedGrouping);
    this.appService.setGrouping(this.selectedGrouping);

  }





  onGroupingChange(groupingStr: string) {

    var groupingType: Grouping | undefined = this.groupingTypes.get(groupingStr)
    if (groupingType == undefined) {
      this.selectedGrouping = Grouping.MONTH;
    } else {
      this.selectedGrouping = groupingType;
    }
    this.appService.setGrouping(this.selectedGrouping);
    this.change.emit(this.selectedGrouping);

  }



}
