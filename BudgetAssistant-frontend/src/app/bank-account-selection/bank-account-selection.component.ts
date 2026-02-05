import {Component, EventEmitter, OnDestroy, OnInit, Output} from '@angular/core';
import {AppService} from '../app.service';
import {Subject, takeUntil} from "rxjs";
import {BankAccountRead} from "@daanvdn/budget-assistant-client";
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
    imports: [MatFormField, MatLabel, MatSelect, NgFor, MatOption, UpperCasePipe, IbanPipe, MatIconModule]
})
export class BankAccountSelectionComponent implements OnInit, OnDestroy {

  private ibanPipe = new IbanPipe();

  selectedBankAccount!: BankAccountRead;
  bankAccounts: BankAccountRead[] = [];
  
  /** Calculated width to fit the longest account number */
  formFieldWidth: string = 'auto';

  @Output() change: EventEmitter<BankAccountRead> = new EventEmitter<BankAccountRead>(true);
  private destroy$ = new Subject<void>();

  constructor(private appService: AppService) {
    this.appService.triggerRefreshBankAccounts();
    this.appService.refreshBankAccountsObservable$.pipe(takeUntil(this.destroy$)).subscribe(result => {
        if (result && result) {
            this.appService.fetchBankAccountsForUser()
                .pipe(takeUntil(this.destroy$))
                .subscribe(result => {
                        if (result == undefined || result.length === 0) {
                            console.warn('No bank accounts found for user');
                            return;
                        }
                        this.bankAccounts = result;
                        this.calculateFormFieldWidth();
                        this.selectedBankAccount = this.bankAccounts[0];
                        if (this.selectedBankAccount && this.selectedBankAccount.accountNumber) {
                            this.appService.setBankAccount(this.selectedBankAccount);
                            this.change.emit(this.selectedBankAccount);
                        }
                        return this.bankAccounts;
                    }
                )


        }

    })
  }


  ngOnInit() {
  }

  ngOnChanges() {
    if (this.selectedBankAccount && this.selectedBankAccount.accountNumber) {
      this.change.emit(this.selectedBankAccount);
      this.appService.setBankAccount(this.selectedBankAccount);
    } else {
      console.error('Selected bank account or account number is undefined in ngOnChanges');
    }
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Calculate the minimum width needed to display the longest account number.
   * Uses a hidden canvas to measure text width accurately.
   */
  private calculateFormFieldWidth(): void {
    if (!this.bankAccounts || this.bankAccounts.length === 0) {
      this.formFieldWidth = 'auto';
      return;
    }

    // Find the longest formatted account number
    let maxLength = 0;
    let longestFormatted = '';
    
    for (const account of this.bankAccounts) {
      if (account.accountNumber) {
        const formatted = this.ibanPipe.transform(account.accountNumber.toUpperCase()) as string;
        if (formatted.length > maxLength) {
          maxLength = formatted.length;
          longestFormatted = formatted;
        }
      }
    }

    if (longestFormatted) {
      // Use canvas to measure text width accurately
      const canvas = document.createElement('canvas');
      const context = canvas.getContext('2d');
      if (context) {
        // Use the same font as Material form fields (Roboto)
        context.font = '16px Roboto, "Helvetica Neue", sans-serif';
        const textWidth = context.measureText(longestFormatted).width;
        // Add padding for Material form field chrome (label, dropdown arrow, padding)
        const paddingAndChrome = 80;
        this.formFieldWidth = `${Math.ceil(textWidth + paddingAndChrome)}px`;
      }
    }
  }

}
