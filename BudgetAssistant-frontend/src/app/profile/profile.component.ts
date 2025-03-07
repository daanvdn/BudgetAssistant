import { Component, OnInit } from '@angular/core';
import {AuthService} from "../auth/auth.service";
import { User} from "../model";
import {FormArray, FormBuilder, FormControl, FormGroup} from "@angular/forms";
import {AppService} from "../app.service";
import {MatTableDataSource} from "@angular/material/table";
import {faSearch} from "@fortawesome/free-solid-svg-icons/faSearch";
import {BankAccount} from "@daanvdn/budget-assistant-client";

@Component({
  selector: 'app-profile',
  templateUrl: './profile.component.html',
  styleUrls: ['./profile.component.scss']
})
export class ProfileComponent implements OnInit {

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
    this.appService.fetchBankAccountsForUser().subscribe(bankAccounts => {
      this.bankAccounts = bankAccounts;
      this.dataSource = new MatTableDataSource(this.bankAccounts);
    });
  }



  saveAlias(bankAccount: BankAccount): void {


    this.appService.saveBankAccountAlias(bankAccount).subscribe(() => {});
  }


  protected readonly faSearch = faSearch;
}
