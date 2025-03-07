import {Component, EventEmitter, OnInit, Output} from '@angular/core';
import {FormBuilder, FormGroup} from '@angular/forms';
import {AppService} from '../app.service';
import {GroupingEnum} from "@daanvdn/budget-assistant-client";

@Component({
  selector: 'grouping-type-selection',
  templateUrl: './grouping-type-selection.component.html',
  styleUrls: ['./grouping-type-selection.component.scss']
})
export class GroupingTypeSelectionComponent implements OnInit {

  groupingTypesFormFieldGroup: FormGroup;

  groupingTypes: Map<string, GroupingEnum> = new Map<string, GroupingEnum>();
  groupingTypeStringValues: string[];
  selectedGrouping!: GroupingEnum;
  @Output() change: EventEmitter<GroupingEnum> = new EventEmitter<GroupingEnum>(true);



  constructor(formBuilder: FormBuilder, private appService: AppService) {

    this.groupingTypesFormFieldGroup = formBuilder.group({ queryForm: "" });
    this.groupingTypes.set("month", GroupingEnum.month)
    this.groupingTypes.set("year", GroupingEnum.year)
    this.groupingTypes.set("quarter", GroupingEnum.quarter)
    this.groupingTypeStringValues = Array.from(this.groupingTypes.keys());
    this.selectedGrouping = GroupingEnum.month;

  }

  ngOnInit() {
    this.change.emit(this.selectedGrouping);
    this.appService.setGrouping(this.selectedGrouping);

  }





  onGroupingChange(groupingStr: string) {

    var groupingType: GroupingEnum | undefined = this.groupingTypes.get(groupingStr)
    if (groupingType == undefined) {
      this.selectedGrouping = GroupingEnum.month;
    } else {
      this.selectedGrouping = groupingType;
    }
    this.appService.setGrouping(this.selectedGrouping);
    this.change.emit(this.selectedGrouping);

  }



}
