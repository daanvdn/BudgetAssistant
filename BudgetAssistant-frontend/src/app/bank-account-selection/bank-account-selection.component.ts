import {Component, EventEmitter, OnDestroy, OnInit, Output} from '@angular/core';
import {FormBuilder, FormGroup} from '@angular/forms';
import {AppService} from '../app.service';
import {Subject, takeUntil} from "rxjs";
import {BankAccount} from "../model";

@Component({
  selector: 'bank-account-selection',
  templateUrl: './bank-account-selection.component.html',
  styleUrls: ['./bank-account-selection.component.scss']
})
export class BankAccountSelectionComponent implements OnInit, OnDestroy {


  bankAccountFormFieldGroup: FormGroup;
  selectedBankAccount!: BankAccount;
  bankAccounts: BankAccount[] = [];

  @Output() change: EventEmitter<BankAccount> = new EventEmitter<BankAccount>(true);
  private destroy$ = new Subject<void>();

  constructor(private appService: AppService, private formBuilder: FormBuilder) {
    this.appService.fetchBankAccountsForUser()
      .pipe(takeUntil(this.destroy$))
      .subscribe(result => {
        if (result == undefined) {
          return;
        }
        this.bankAccounts = result
        this.selectedBankAccount = this.bankAccounts[0];
        this.appService.setBankAccount(this.selectedBankAccount);
        this.change.emit(this.selectedBankAccount);
        return this.bankAccounts;

      }
    )
    this.bankAccountFormFieldGroup = formBuilder.group({queryForm: ""});
  }


  ngOnInit() {
  }

  ngOnChanges() {
    this.change.emit(this.selectedBankAccount);
    this.appService.setBankAccount(this.selectedBankAccount);
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

}
