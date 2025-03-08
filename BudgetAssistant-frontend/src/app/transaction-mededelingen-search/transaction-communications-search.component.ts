import { Component, EventEmitter, OnInit, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatFormField, MatLabel } from '@angular/material/form-field';
import { MatInput } from '@angular/material/input';

@Component({
    selector: 'app-transaction-communications-search',
    templateUrl: './transaction-communications-search.component.html',
    styleUrls: ['./transaction-communications-search.component.scss'],
    standalone: true,
    imports: [FormsModule, MatFormField, MatLabel, MatInput]
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
