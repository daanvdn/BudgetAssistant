import {DatePipe} from '@angular/common';
import {AfterViewInit, Component, OnInit, ViewChild} from '@angular/core';
import {MatDialog} from '@angular/material/dialog';
import {MatPaginator} from '@angular/material/paginator';
import {MatRadioChange} from '@angular/material/radio';
import {MatSort} from '@angular/material/sort';
import {MatTable} from '@angular/material/table';
import {PaginationDataSource} from 'ngx-pagination-data-source';
import {AppService} from '../app.service';
import {
  AmountType,
  CompositeTransactionsFileUploadResponse, EMPTY_TRANSACTION_QUERY, FileWrapper, inferAmountType
} from '../model';
import {BankAccountSelectionComponent} from '../bank-account-selection/bank-account-selection.component';
import {TransactionSearchDialogComponent} from '../transaction-search-dialog/transaction-search-dialog.component';
import {AuthService} from "../auth/auth.service";
import {HttpEventType, HttpResponse} from "@angular/common/http";
import {ErrorDialogService} from "../error-dialog/error-dialog.service";
import {faTag} from "@fortawesome/free-solid-svg-icons";
import {Router} from "@angular/router";
import {Transaction, TransactionQuery, TransactionTypeEnum} from '@daanvdn/budget-assistant-client';


enum ViewType {
  INITIAL_VIEW = "INITIAL_VIEW",
  RUN_QUERY = "RUN_QUERY",
  SHOW_ALL = "SHOW_ALL",
  UPLOAD_TRANSACTIONS = "UPLOAD_TRANSACTIONS",
}


@Component({
  selector: 'app-transactions',
  templateUrl: './transactions.component.html',
  styleUrls: ['./transactions.component.scss']

})
export class TransactionsComponent implements OnInit, AfterViewInit {




  //table stuff
  @ViewChild(MatPaginator, { static: false }) paginator!: MatPaginator;
  @ViewChild(MatSort, { static: false }) sort!: MatSort;
  @ViewChild(MatTable) table!: MatTable<Transaction>;
  @ViewChild(BankAccountSelectionComponent) accountSelectionComponent!: BankAccountSelectionComponent;
  private currentSort?: any;


  filesAreUploading = false; // Add this line
  transactionToManuallyReview!: Number;

  dataSource: PaginationDataSource<Transaction, TransactionQuery>;
  displayedColumns = [
    "bookingDate",
    "counterparty",
    "transaction",
    "amount",
    "transactionType"
  ];
  transactionQuery?: TransactionQuery;
  transactionQueryAsJson?: string;
  selectedAccount?:string;

  @ViewChild('fileInput') fileInput: any;

  viewType: ViewType = ViewType.INITIAL_VIEW;


  constructor(private appService: AppService, private authService: AuthService, public dialog: MatDialog,
              public datepipe: DatePipe, private errorDialogService: ErrorDialogService, private router: Router) {

    let rekening = undefined
    this.dataSource = this.initDataSource(rekening);
    this.appService.selectedBankAccountObservable$.subscribe(bankAccount => {
      if (bankAccount) {
        this.appService.countTransactionToManuallyReview(bankAccount).subscribe(count => {
          this.transactionToManuallyReview = count;

        });
      }
    })

  }

  showTransactionsToManuallyReview(){

    this.router.navigate(['/categorieën']);
  }

  onClickFileInputButton(): void {
    this.fileInput.nativeElement.click();
  }

  onChangeFileInput(): void {
    this.filesAreUploading = true;
    let files: File[] = this.fileInput.nativeElement.files;
    let fileWrapperArray: FileWrapper[] = [];

    for (let index = 0; index < files.length; index++) {
      const file = files[index];
      fileWrapperArray.push({ file: file, inProgress: false, progress: 0, failed: false });
    }

    let currentUser = this.authService.getUser();
    if (!currentUser || !currentUser.userName) {
      this.errorDialogService.openErrorDialog("Cannot upload transactions!", "User is not defined");
      return;
    }
    this.appService.uploadTransactionFiles(fileWrapperArray, currentUser.userName).subscribe(result => {

      if (result.type === HttpEventType.Response) {

        let response = result as HttpResponse<CompositeTransactionsFileUploadResponse>
        let uploadTimestamp = response.body?.uploadTimestamp;
        if (uploadTimestamp === undefined) {
          this.filesAreUploading = false;
          throw new Error("uploadTimestamp is undefined");
        }

        let newSort;
        if (this.currentSort !== undefined) {
          newSort = this.currentSort;
        } else {

          newSort = {property: 'bookingDate', order: 'desc'}
          this.currentSort = newSort;
        }

        let transactionQuery: TransactionQuery = {
          transactionType: TransactionTypeEnum.BOTH,
          counterpartyName: undefined,
          minAmount: undefined,
          maxAmount: undefined,
          accountNumber: undefined,
          category: undefined,
          counterpartyAccountNumber: undefined,
          startDate: undefined,
          endDate: undefined,
          transactionOrCommunication: undefined,
          uploadTimestamp: uploadTimestamp
        }

        this.dataSource = new PaginationDataSource<Transaction, TransactionQuery>(
          (request, query) => {
            request.size = 50;
            return this.appService.pageTransactions(request, query);
          },
          newSort, transactionQuery
        );
        this.viewType = ViewType.UPLOAD_TRANSACTIONS;
        this.filesAreUploading = false;


      }


    })






  }


  translateBooleanToDutchJaNee(b: Boolean | undefined): string {
    if (b === undefined) {
      return "N/A";
    }

    if (b) {
      return "ja";
    }

    return "nee";
  }
  displayNumberOrNA(number: Number | undefined): string {
    if (number === undefined) {
      return "N/A";
    }

    return number.toString();
  }
  displayStringOrNA(s: string | undefined | null): string {
    if (s === undefined || s === null) {
      return "N/A";
    }

    return s;
  }

  amountType(transaction: Transaction): AmountType {
    if (transaction.amount === undefined || transaction.amount === null) {
      return AmountType.BOTH;
    }
    return inferAmountType(transaction.amount)


  }
  displayDateOrNA(s: Date | undefined | null): string | null {
    if (s === undefined || s === null) {
      return "N/A";
    }
    return this.datepipe.transform(s, 'dd-MM-yyyy')

  }

  openDialog(): void {


    const dialogRef = this.dialog.open(TransactionSearchDialogComponent, {
      restoreFocus: false
    });

    dialogRef.afterClosed().subscribe(result => {
      // console.log('The dialog was closed');
      if (result === undefined) {
        return;
      } else {
        this.transactionQuery = result;
        if (this.transactionQuery != undefined){
          this.transactionQuery.accountNumber = this.selectedAccount;

        }

      }
      if (this.transactionQuery !== undefined) {
        this.transactionQueryAsJson = JSON.stringify(this.transactionQuery)
      }
      this.doQuery(this.transactionQuery)
    });

  }

  handleAccountChange(){
    this.selectedAccount = this.accountSelectionComponent.selectedBankAccount.accountNumber
    if (this.selectedAccount === undefined || this.selectedAccount === this.appService.DUMMY_BANK_ACCOUNT) {
      return;
    }
    this.transactionQuery  = {
      transactionType: TransactionTypeEnum.BOTH,
      counterpartyName: undefined,
      minAmount: undefined,
      maxAmount: undefined,
      accountNumber: this.selectedAccount,
      category: undefined,
      counterpartyAccountNumber: undefined,
      startDate: undefined,
      endDate: undefined,
      transactionOrCommunication: undefined,
      uploadTimestamp: undefined

    }
    this.doQuery(this.transactionQuery)

  }
  showAllTransactions() {
    this.dataSource = this.initDataSource(this.selectedAccount);
    this.transactionQuery = undefined;
    this.viewType = ViewType.SHOW_ALL;

  }
  ngAfterViewInit(): void {

  }


  ngOnInit() {

  }




  private initDataSource(account:string | undefined): PaginationDataSource<Transaction, TransactionQuery> {
    let query = {} as TransactionQuery;
    if(account !== undefined){
      query.accountNumber = account;

    }
    return new PaginationDataSource<Transaction, TransactionQuery>(
      (request, query) => {
        request.size = 50;
        return this.appService.pageTransactions(request, query);
      },
      {property: 'bookingDate', order: 'desc'}, query
    );
  }


  saveTransaction(transaction: Transaction) {
    this.appService.saveTransaction(transaction)
  }

  setIsRecurring(transaction: Transaction, event: MatRadioChange) {
    let value: boolean = event.value;
    transaction.isRecurring = value;
    this.saveTransaction(transaction);
  }


  setIsAdvanceSharedAccount(transaction: Transaction, event: MatRadioChange) {
    let value: boolean = event.value;
    transaction.isAdvanceSharedAccount = value;
    this.saveTransaction(transaction);
  }


  setCategory(transaction: Transaction, selectedCategoryQualifiedNameStr: string) {
    transaction.category = {qualifiedName:selectedCategoryQualifiedNameStr};
    this.saveTransaction(transaction);
  }

  sortBy(event: any) {
    let key = event.active;
    let direction = event.direction;
    this.currentSort = {
      property: key,
      order: direction || "ASC"

    };
    this.dataSource.sortBy(this.currentSort);
  }

  doQuery(transactionQuery: TransactionQuery | undefined): void {
    if (transactionQuery === undefined) {
      return;
    }

    let newSort;
    if (this.currentSort !== undefined) {
      newSort = this.currentSort;
    } else {

      newSort = { property: 'bookingDate', order: 'desc' }
      this.currentSort = newSort;
    }

    this.dataSource = new PaginationDataSource<Transaction, TransactionQuery>(
      (request, query) => {
        request.size = 50;
        return this.appService.pageTransactions(request, query);
      },
      newSort, transactionQuery
    );

    this.viewType = ViewType.RUN_QUERY;
  }


  protected readonly ViewType = ViewType;
  protected readonly faTag = faTag;

  getNrOfTransactionsToManuallyReview(): string {
    if (this.transactionToManuallyReview){

      return  this.transactionToManuallyReview.toString();
    }

    return "";


  }

  getNrOfTransactionsToManuallyReviewTooltip() : string {
    if (this.transactionToManuallyReview){

      return `You have ${this.transactionToManuallyReview} transactions to manually review`;
    }

    return "";
  }
}





