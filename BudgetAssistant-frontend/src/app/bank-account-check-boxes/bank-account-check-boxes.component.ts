import {Component, EventEmitter, OnDestroy, OnInit, Output} from '@angular/core';
import {AppService} from "../app.service";
import {Subject, takeUntil} from "rxjs";
import { FormBuilder, FormGroup, FormArray, FormsModule, ReactiveFormsModule } from "@angular/forms";
import { BankAccount } from '@daanvdn/budget-assistant-client';
import { NgFor, UpperCasePipe } from '@angular/common';
import { MatCheckbox } from '@angular/material/checkbox';

@Component({
    selector: 'bank-account-check-boxes',
    templateUrl: './bank-account-check-boxes.component.html',
    styleUrls: ['./bank-account-check-boxes.component.scss'],
    standalone: true,
    imports: [FormsModule, ReactiveFormsModule, NgFor, MatCheckbox, UpperCasePipe]
})
export class BankAccountCheckBoxesComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  bankAccounts: BankAccount[] = [];
  form: FormGroup;

  @Output() change: EventEmitter<BankAccount[]> = new EventEmitter<BankAccount[]>();

  constructor(private appService: AppService, private formBuilder: FormBuilder) {
    this.form = this.formBuilder.group({
      bankAccounts: new FormArray([])
    });

    this.appService.fetchBankAccountsForUser()
      .pipe(takeUntil(this.destroy$))
      .subscribe(result => {
        if (result == undefined) {
          return;
        }
        this.bankAccounts = result;
        const bankAccountsFormArray = this.form.get('bankAccounts') as FormArray;
        this.bankAccounts.forEach(() => {
          bankAccountsFormArray.push(this.formBuilder.control(true));
        });
      });

  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  ngOnInit(): void {
    const bankAccountsFormArray = this.form.get('bankAccounts') as FormArray;
    bankAccountsFormArray.valueChanges.subscribe(() => {
      this.emitSelectedAccounts();
    });
  }

  getFormArrayControls() {
    return (this.form.get('bankAccounts') as FormArray).controls;
  }

  emitSelectedAccounts() {
    const formArrayControls = this.getFormArrayControls();
    let selectedBankAccounts: BankAccount[] = [];

    this.bankAccounts.forEach((bankAccount, index) => {
      let selected: boolean = formArrayControls[index].value;
      if (selected){
        selectedBankAccounts.push(bankAccount);
      }
      });

    this.change.emit(selectedBankAccounts);
  }

}
