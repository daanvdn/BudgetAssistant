import {Component, EventEmitter, OnInit, Output} from '@angular/core';
import { MatButtonToggleChange, MatButtonToggleGroup, MatButtonToggle } from "@angular/material/button-toggle";
import {TransactionType} from "../model";
import {AppService} from "../app.service";
import {TransactionTypeEnum} from "@daanvdn/budget-assistant-client";

@Component({
    selector: 'expenses-revenue-toggle',
    templateUrl: './expenses-revenue-toggle.component.html',
    styleUrls: ['./expenses-revenue-toggle.component.scss'],
    standalone: true,
    imports: [MatButtonToggleGroup, MatButtonToggle]
})
export class ExpensesRevenueToggleComponent implements OnInit {

  @Output() change: EventEmitter<TransactionType> = new EventEmitter<TransactionType>(true);


  constructor(private appService: AppService) { }

  ngOnInit(): void {
    this.change.emit(TransactionType.EXPENSES);
    this.appService.setTransactionType(TransactionTypeEnum.EXPENSES);
  }
  onToggleChange($event: MatButtonToggleChange) {
    const value = $event.value;
    if (value === "expenses") {
      this.change.emit(TransactionType.EXPENSES);
      this.appService.setTransactionType(TransactionTypeEnum.EXPENSES);
    }
    else if (value === "revenue") {
      this.change.emit(TransactionType.REVENUE);
      this.appService.setTransactionType(TransactionTypeEnum.REVENUE);
    }
    else {
      throw new Error("Unknown value " + value);
    }
  }
}
