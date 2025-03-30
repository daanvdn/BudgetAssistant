import {Component, EventEmitter, OnDestroy, OnInit, Output} from '@angular/core';
import { FormBuilder, FormGroup, FormsModule, ReactiveFormsModule } from '@angular/forms';
import {AppService} from '../app.service';
import {Subject, takeUntil} from "rxjs";
import {BankAccount} from "@daanvdn/budget-assistant-client";
import { MatFormField, MatLabel } from '@angular/material/form-field';
import { MatSelect } from '@angular/material/select';
import { NgFor, UpperCasePipe } from '@angular/common';
import { MatOption } from '@angular/material/core';
import { IbanPipe } from '../iban.pipe';
import {MatIconModule} from "@angular/material/icon";

@Component({
    selector: 'bank-account-selection',
    templateUrl: './bank-account-selection.component.html',
    styleUrls: ['./bank-account-selection.component.scss'],
    standalone: true,
    imports: [FormsModule, ReactiveFormsModule, MatFormField, MatLabel, MatSelect, NgFor, MatOption, UpperCasePipe, IbanPipe, MatIconModule]
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
