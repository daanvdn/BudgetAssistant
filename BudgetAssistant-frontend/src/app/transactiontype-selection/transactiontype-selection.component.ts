import { Component, EventEmitter, OnInit, Output, ViewChild } from '@angular/core';
import { FormBuilder, FormGroup, FormsModule } from '@angular/forms';
import { NgSelectComponent } from '@ng-select/ng-select';
import { first, Observable, of } from 'rxjs';
import { TransactionType } from '../model';
import { MatFormField, MatLabel } from '@angular/material/form-field';
import { MatInput } from '@angular/material/input';
import { AsyncPipe } from '@angular/common';
import {TransactionTypeEnum} from "@daanvdn/budget-assistant-client";

@Component({
    selector: 'app-transactiontype-selection',
    templateUrl: './transactiontype-selection.component.html',
    styleUrls: ['./transactiontype-selection.component.scss'],
    standalone: true,
    imports: [MatFormField, MatLabel, MatInput, FormsModule, NgSelectComponent, AsyncPipe]
})


export class TransactiontypeSelectionComponent implements OnInit {



  transactionTypes: Map<string, TransactionTypeEnum> = new Map<string, TransactionTypeEnum>();
  transactionTypesObservable!: Observable<string[]>;
  selectedTransactionType!: TransactionTypeEnum;
  minAmount!:number;
  maxAmount!:number;
  @ViewChild(NgSelectComponent) ngSelect!:NgSelectComponent;




  @Output() transactionTypeChange: EventEmitter<boolean> = new EventEmitter<boolean>();
  constructor(private formBuilder: FormBuilder) {
  }

  ngOnInit() {
    this.transactionTypes.set("in- & uitkomsten", TransactionTypeEnum.BOTH)
    this.transactionTypes.set("uitgaven", TransactionTypeEnum.EXPENSES)
    this.transactionTypes.set("inkomsten", TransactionTypeEnum.REVENUE)
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

  private getSelectedTransactionType(): TransactionTypeEnum | null | undefined{
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
