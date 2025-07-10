import {Component, effect, Injector, OnInit, inject, runInInjectionContext} from '@angular/core';
import {AuthService} from "../auth/auth.service";
import {User} from "../model";
import {FormBuilder, FormGroup, FormsModule, ReactiveFormsModule} from "@angular/forms";
import {AppService} from "../app.service";
import {
  MatCell,
  MatCellDef,
  MatColumnDef,
  MatHeaderCell,
  MatHeaderCellDef,
  MatHeaderRow,
  MatHeaderRowDef,
  MatRow,
  MatRowDef,
  MatTable,
  MatTableDataSource
} from "@angular/material/table";
import {faSearch} from "@fortawesome/free-solid-svg-icons/faSearch";
import {BankAccount} from "@daanvdn/budget-assistant-client";
import {MatToolbar} from '@angular/material/toolbar';
import {MatCard, MatCardContent} from '@angular/material/card';
import {MatFormField, MatSuffix} from '@angular/material/form-field';
import {MatInput} from '@angular/material/input';
import {MatIconButton} from '@angular/material/button';
import {MatIcon} from '@angular/material/icon';
import {NgIf, UpperCasePipe} from '@angular/common';
import {IbanPipe} from '../iban.pipe';


@Component({
    selector: 'app-profile',
    templateUrl: './profile.component.html',
    styleUrls: ['./profile.component.scss'],
    standalone: true,
    imports: [MatToolbar, FormsModule, ReactiveFormsModule, MatCard, MatCardContent, MatFormField, MatInput, MatIconButton, MatSuffix, MatIcon, NgIf, MatTable, MatColumnDef, MatHeaderCellDef, MatHeaderCell, MatCellDef, MatCell, MatHeaderRowDef, MatHeaderRow, MatRowDef, MatRow, UpperCasePipe, IbanPipe]
})
export class ProfileComponent implements OnInit {
  //inject an Injector instance
  private injector: Injector = inject(Injector); // Define injector instance




  currentUser!: User;
  hidePassword = true;
  form: FormGroup;
  bankAccounts!: BankAccount[];
  displayedColumns: string[] = ['accountNumber', 'alias', 'saveOrEditButton'];
  dataSource!: MatTableDataSource<BankAccount>;


  constructor(private authService : AuthService, private fb: FormBuilder, private appService: AppService) {
    this.form = this.fb.group({
      password: ""
    });



  }



  ngOnInit(): void {
    this.authService.getUserObservable().subscribe(u => {
      this.currentUser = u;
    })

    runInInjectionContext(this.injector, (): void => { // Use effect to react to query data changes
      effect(() => {
        const bankAccountsData = this.appService.bankAccountsQuery.data();
        if (bankAccountsData) {
          this.bankAccounts = bankAccountsData;
          this.dataSource = new MatTableDataSource(this.bankAccounts);
        }
      });
    })


  }



  saveAlias(bankAccount: BankAccount): void {


    this.appService.saveBankAccountAlias(bankAccount).subscribe(() => {});
  }


  protected readonly faSearch = faSearch;
}
