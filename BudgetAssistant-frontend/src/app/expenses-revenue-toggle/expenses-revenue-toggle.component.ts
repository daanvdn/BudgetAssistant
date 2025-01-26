import {Component, EventEmitter, OnInit, Output} from '@angular/core';
import {MatButtonToggleChange} from "@angular/material/button-toggle";
import {TransactionType} from "../model";
import {AppService} from "../app.service";

@Component({
  selector: 'expenses-revenue-toggle',
  templateUrl: './expenses-revenue-toggle.component.html',
  styleUrls: ['./expenses-revenue-toggle.component.scss']
})
export class ExpensesRevenueToggleComponent implements OnInit {

  @Output() change: EventEmitter<TransactionType> = new EventEmitter<TransactionType>(true);


  constructor(private appService: AppService) { }

  ngOnInit(): void {
    this.change.emit(TransactionType.EXPENSES);
    this.appService.setTransactionType(TransactionType.EXPENSES);
  }
  onToggleChange($event: MatButtonToggleChange) {
    const value = $event.value;
    if (value === "expenses") {
      this.change.emit(TransactionType.EXPENSES);
      this.appService.setTransactionType(TransactionType.EXPENSES);
    }
    else if (value === "revenue") {
      this.change.emit(TransactionType.REVENUE);
      this.appService.setTransactionType(TransactionType.REVENUE);
    }
    else {
      throw new Error("Unknown value " + value);
    }
  }
}
