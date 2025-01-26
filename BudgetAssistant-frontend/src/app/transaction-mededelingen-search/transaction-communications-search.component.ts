import { Component, EventEmitter, OnInit, Output } from '@angular/core';

@Component({
  selector: 'app-transaction-communications-search',
  templateUrl: './transaction-communications-search.component.html',
  styleUrls: ['./transaction-communications-search.component.scss']
})
export class TransactionCommunicationsSearchComponent implements OnInit {

  searchText!: string;
  @Output() change: EventEmitter<boolean> = new EventEmitter<boolean>();
  constructor() { }

  ngOnInit() {
  }

  onSearchTextChange(){
    this.change.emit();
  }


}
