import {Component, effect, EventEmitter, OnInit, Output, ViewChild} from '@angular/core';
import {NgSelectComponent} from '@ng-select/ng-select';
import {Observable} from 'rxjs';
import {AppService} from '../app.service';
import { FormsModule } from '@angular/forms';
import { AsyncPipe } from '@angular/common';

@Component({
    selector: 'app-counterparty-name-selection',
    templateUrl: './counterparty-name-selection.component.html',
    styleUrls: ['./counterparty-name-selection.component.scss'],
    standalone: true,
    imports: [NgSelectComponent, FormsModule, AsyncPipe]
})
export class CounterpartyNameSelectionComponent implements OnInit {

  @Output() change: EventEmitter<boolean> = new EventEmitter<boolean>();
  @ViewChild(NgSelectComponent) ngSelect!:NgSelectComponent;

  selectedCounterpartyName!: string;
  distinctCounterpartyNames!: Observable<string[]>;



  constructor(private appService: AppService) {



  }




  ngOnInit() {

    effect(() => {
        const selectedBankAccount = this.appService.selectedBankAccount();
        if (selectedBankAccount) {
            this.distinctCounterpartyNames = this.appService.getDistinctCounterpartyNames(selectedBankAccount.accountNumber);
        }
    })

  }



  counterpartySelectionChanges() {

    let sel = this.getSelectedCounterparty();
    if(sel !== undefined && sel !== null){
      this.selectedCounterpartyName = sel;
      this.change.emit(true);
    }
  }

  /**
   * we cannot use two-way binding on ngModel because of how ng-select works. so this is a workaround
   * @returns
   */

  private getSelectedCounterparty(): string | null | undefined{
    let selectedItems = this.ngSelect.selectedItems;
    if (selectedItems === null || selectedItems.length ===0){
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
