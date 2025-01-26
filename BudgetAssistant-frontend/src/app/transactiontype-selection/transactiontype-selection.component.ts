import { Component, EventEmitter, OnInit, Output, ViewChild } from '@angular/core';
import {FormBuilder, FormGroup } from '@angular/forms';
import { NgSelectComponent } from '@ng-select/ng-select';
import { first, Observable, of } from 'rxjs';
import { TransactionType } from '../model';

@Component({
  selector: 'app-transactiontype-selection',
  templateUrl: './transactiontype-selection.component.html',
  styleUrls: ['./transactiontype-selection.component.scss']
})


export class TransactiontypeSelectionComponent implements OnInit {



  transactionTypes: Map<string, TransactionType> = new Map<string, TransactionType>();
  transactionTypesObservable!: Observable<string[]>;
  selectedTransactionType!: TransactionType;
  minAmount!:number;
  maxAmount!:number;
  @ViewChild(NgSelectComponent) ngSelect!:NgSelectComponent;




  @Output() transactionTypeChange: EventEmitter<boolean> = new EventEmitter<boolean>();
  constructor(private formBuilder: FormBuilder) {
  }

  ngOnInit() {
    this.transactionTypes.set("in- & uitkomsten", TransactionType.BOTH)
    this.transactionTypes.set("uitgaven", TransactionType.EXPENSES)
    this.transactionTypes.set("inkomsten", TransactionType.REVENUE)
    this.transactionTypesObservable = of(Array.from(this.transactionTypes.keys()))
  }

  public onSelectionChange(): void{
    let sel = this.getSelectedTransactionType();
    if (sel !== null && sel != undefined){
      this.selectedTransactionType = sel;
      this.transactionTypeChange.emit();
    }
  }

  /**
   * we cannot use two-way binding on ngModel because of how ng-select works. so this is a workaround
   * @returns
   */

  private getSelectedTransactionType(): TransactionType | null | undefined{
    let selectedItems = this.ngSelect.selectedItems;
    if (selectedItems == null || selectedItems.length ===0){
      return null;
    }
    if( selectedItems.length != 1){
      throw new Error("only 1 item can be selected!")
    }
    let firstValue: string | undefined = selectedItems[0].value;
    if (firstValue === undefined){
      throw new Error("value must not be undefined!")
    }

    return this.transactionTypes.get(firstValue);




  }


}
