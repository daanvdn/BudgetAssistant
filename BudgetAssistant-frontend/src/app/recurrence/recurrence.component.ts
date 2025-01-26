import { Component, EventEmitter, OnInit, Output } from '@angular/core';
import { AppService } from '../app.service';

@Component({
  selector: 'app-recurrence',
  templateUrl: './recurrence.component.html',
  styleUrls: ['./recurrence.component.scss']
})
export class RecurrenceComponent implements OnInit {

  types = ["recurrent", "non-recurrent", "both"];
  selectedExpensesRecurrence:string = "both";
  selectedRevenueRecurrence:string = "both";

  @Output() expensesRecurrenceChangeEmitter: EventEmitter<boolean> = new EventEmitter<boolean>();
  @Output() revenueRecurrenceChangeEmitter: EventEmitter<boolean> = new EventEmitter<boolean>();

  constructor(private appService: AppService) {
    this.selectedExpensesRecurrence = "both"
    this.appService.setExpensesRecurrence(this.selectedExpensesRecurrence);
    this.appService.setRevenueRecurrence(this.selectedRevenueRecurrence);
  }

  ngOnInit() {
  }


  onUitgavenChange(){
    this.expensesRecurrenceChangeEmitter.emit();
    this.appService.setExpensesRecurrence(this.selectedExpensesRecurrence);
  }
  onInkomstenChange(){
    this.revenueRecurrenceChangeEmitter.emit();
    this.appService.setRevenueRecurrence(this.selectedRevenueRecurrence);
  }

}
