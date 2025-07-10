import {Component, effect, EventEmitter, OnInit, Output, ViewChild} from '@angular/core';
import {NgSelectComponent} from '@ng-select/ng-select';
import {Observable} from 'rxjs';
import {AppService} from '../app.service';
import { FormsModule } from '@angular/forms';
import { AsyncPipe } from '@angular/common';

@Component({
    selector: 'app-counterparty-account-number-selection',
    templateUrl: './counterparty-account-number-selection.component.html',
    styleUrls: ['./counterparty-account-number-selection.component.scss'],
    standalone: true,
    imports: [NgSelectComponent, FormsModule, AsyncPipe]
})
export class CounterpartyAccountNumberSelectionComponent implements OnInit {

  @Output() change: EventEmitter<boolean> = new EventEmitter<boolean>();
  @ViewChild(NgSelectComponent) ngSelect!:NgSelectComponent;

  selectedCounterpartAccountNumber!: string;
  distinctCounterpartAccountNumbers!: Observable<string[]>;

  constructor(private appService: AppService) {

  }

  ngOnInit() {
    effect(() => {
        const selectedBankAccount = this.appService.selectedBankAccount();
        if (selectedBankAccount) {
          this.distinctCounterpartAccountNumbers = this.appService.getDistinctCounterpartyAccounts(selectedBankAccount.accountNumber);

        }
    });



  }



  accountCounterpartySelectionChanges() {
    let sel = this.getSelectedCounterpartAccountNumber()
    if(sel !== null && sel !== undefined){
      this.selectedCounterpartAccountNumber = sel;
      this.change.emit();
    }
  }

  /**
   * we cannot use two-way binding on ngModel because of how ng-select works. so this is a workaround
   * @returns
   */
  private getSelectedCounterpartAccountNumber(): string | null | undefined{
    let selectedItems = this.ngSelect.selectedItems;
    if (selectedItems == null){
      return null;
    }
    if( selectedItems.length != 1){
      throw new Error("only 1 item can be selected!")
    }
    let firstValue: string | undefined = selectedItems[0].value;
    if (firstValue === undefined){
      throw new Error("value must not be undefined!")
    }

    return firstValue;




  }

}
