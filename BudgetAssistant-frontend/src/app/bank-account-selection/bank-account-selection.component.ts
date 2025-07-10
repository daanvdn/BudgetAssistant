import {Component, EventEmitter, OnDestroy, OnInit, Output, effect} from '@angular/core';
import {FormBuilder, FormGroup, FormsModule, ReactiveFormsModule} from '@angular/forms';
import {AppService} from '../app.service';
import {Subject, takeUntil} from "rxjs";
import {BankAccount} from "@daanvdn/budget-assistant-client";
import {MatFormField, MatLabel} from '@angular/material/form-field';
import {MatSelect} from '@angular/material/select';
import {NgFor, UpperCasePipe} from '@angular/common';
import {MatOption} from '@angular/material/core';
import {IbanPipe} from '../iban.pipe';
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
        this.appService.triggerRefreshBankAccounts();
        this.bankAccountFormFieldGroup = formBuilder.group({queryForm: ""});
        effect(() => {
            const bankAccountsData = this.appService.bankAccountsQuery.data();
            const isSuccess = this.appService.bankAccountsQuery.isSuccess();

            if (isSuccess && bankAccountsData) {
                if (bankAccountsData.length === 0) {
                    console.warn('No bank accounts found for user');
                    return;
                }

                this.bankAccounts = bankAccountsData;
                this.selectedBankAccount = this.bankAccounts[0];

                if (this.selectedBankAccount && this.selectedBankAccount.accountNumber) {
                    this.appService.setBankAccount(this.selectedBankAccount);
                    this.change.emit(this.selectedBankAccount);
                }
            }
        }, {allowSignalWrites: true});
    }


    ngOnInit() {
    }

    ngOnChanges() {
        if (this.selectedBankAccount && this.selectedBankAccount.accountNumber) {
            this.change.emit(this.selectedBankAccount);
            this.appService.setBankAccount(this.selectedBankAccount);
        }
        else {
            console.error('Selected bank account or account number is undefined in ngOnChanges');
        }
    }

    ngOnDestroy() {
        this.destroy$.next();
        this.destroy$.complete();
    }

}
