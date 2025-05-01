import { DatePipe, NgIf, AsyncPipe, TitleCasePipe } from '@angular/common';
import {AfterViewInit, Component, Input, OnInit, ViewChild} from '@angular/core';
import {MatDialog} from '@angular/material/dialog';
import {MatPaginator} from '@angular/material/paginator';
import { MatRadioChange, MatRadioGroup, MatRadioButton } from '@angular/material/radio';
import { MatSort, MatSortHeader } from '@angular/material/sort';
import { MatTable, MatColumnDef, MatHeaderCellDef, MatHeaderCell, MatCellDef, MatCell, MatHeaderRowDef, MatHeaderRow, MatRowDef, MatRow } from '@angular/material/table';
import {PaginationDataSource} from 'ngx-pagination-data-source';
import {AppService} from '../app.service';
import {
  AmountType, CategoryMap,
  CompositeTransactionsFileUploadResponse,  FileWrapper, inferAmountType
} from '../model';
import {BankAccountSelectionComponent} from '../bank-account-selection/bank-account-selection.component';
import {TransactionSearchDialogComponent} from '../transaction-search-dialog/transaction-search-dialog.component';
import {AuthService} from "../auth/auth.service";
import { HttpEventType, HttpResponse } from "@angular/common/http";
import {ErrorDialogService} from "../error-dialog/error-dialog.service";
import {faTag} from "@fortawesome/free-solid-svg-icons";
import {Router} from "@angular/router";
import {Transaction, TransactionQuery, TransactionTypeEnum} from '@daanvdn/budget-assistant-client';
import { MatToolbar } from '@angular/material/toolbar';
import { MatProgressSpinner } from '@angular/material/progress-spinner';
import { MatButton } from '@angular/material/button';
import { MatIcon } from '@angular/material/icon';
import { MatTooltip } from '@angular/material/tooltip';
import { MatBadge } from '@angular/material/badge';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import { CategoryTreeDropdownComponent } from '../category-tree-dropdown/category-tree-dropdown.component';
import { DateUtilsService } from '../shared/date-utils.service';


enum ViewType {
  INITIAL_VIEW = "INITIAL_VIEW",
  RUN_QUERY = "RUN_QUERY",
  SHOW_ALL = "SHOW_ALL",
  UPLOAD_TRANSACTIONS = "UPLOAD_TRANSACTIONS",
}


@Component({
    selector: 'app-transactions',
    templateUrl: './transactions.component.html',
    styleUrls: ['./transactions.component.scss'],
    standalone: true,
    imports: [MatToolbar, NgIf, MatProgressSpinner, BankAccountSelectionComponent, MatButton, MatIcon, MatTooltip, MatBadge, FaIconComponent, MatPaginator, MatTable, MatSort, MatColumnDef, MatHeaderCellDef, MatHeaderCell, MatSortHeader, MatCellDef, MatCell, CategoryTreeDropdownComponent, MatRadioGroup, MatRadioButton, MatHeaderRowDef, MatHeaderRow, MatRowDef, MatRow, AsyncPipe, TitleCasePipe, DatePipe]
})
export class TransactionsComponent implements OnInit, AfterViewInit {
  protected readonly ViewType = ViewType;
  protected readonly faTag = faTag;


  //table stuff
  @ViewChild(MatPaginator, { static: false }) paginator!: MatPaginator;
  @ViewChild(MatSort, { static: false }) sort!: MatSort;
  @ViewChild(MatTable) table!: MatTable<Transaction>;
  @ViewChild(BankAccountSelectionComponent) accountSelectionComponent!: BankAccountSelectionComponent;
  private currentSort?: any;


  filesAreUploading = false; // Add this line
  transactionToManuallyReview!: number;

  @Input() dataSource!: PaginationDataSource<Transaction, TransactionQuery>;
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
  categoryMap?: CategoryMap;


  constructor(private appService: AppService, private authService: AuthService, public dialog: MatDialog,
              public datepipe: DatePipe, private errorDialogService: ErrorDialogService, private router: Router,
              private dateUtils: DateUtilsService) {

    // Only initialize dataSource if it's not provided via @Input()
    if (!this.dataSource) {
      let account = undefined;
      this.dataSource = this.initDataSource(account);
    }
    this.appService.categoryMapObservable$.subscribe(categoryMap => {
      this.categoryMap = categoryMap;
    })

    this.appService.selectedBankAccountObservable$.subscribe(bankAccount => {
      if (bankAccount && bankAccount.accountNumber) {
        this.appService.countTransactionToManuallyReview(bankAccount).subscribe(count => {
          this.transactionToManuallyReview = count.valueOf();
        });
      } else {
        // Set a default value if bankAccount or accountNumber is undefined
        this.transactionToManuallyReview = 0;
      }
    })

  }

  showTransactionsToManuallyReview(){
    // Check if there are transactions to manually review before navigating
    if (this.transactionToManuallyReview !== undefined && 
        this.transactionToManuallyReview !== null && 
        this.transactionToManuallyReview > 0) {
      this.router.navigate(['/categorieën']);
    } else {
      console.error('No transactions to manually review or count is undefined');
    }
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
          categoryId: undefined,
          counterpartyAccountNumber: undefined,
          startDate: undefined,
          endDate: undefined,
          transactionOrCommunication: undefined,
          uploadTimestamp: uploadTimestamp
        }

        this.dataSource = new PaginationDataSource<Transaction, TransactionQuery>(
          (request:any, query:any) => {
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

  parseDate(dateStr: string | undefined | null): Date | null {
    return this.dateUtils.parseDate(dateStr);
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
    // Check if selectedBankAccount exists before accessing its properties
    if (!this.accountSelectionComponent || !this.accountSelectionComponent.selectedBankAccount) {
      console.error('Selected bank account is undefined in handleAccountChange');
      return;
    }

    this.selectedAccount = this.accountSelectionComponent.selectedBankAccount.accountNumber;
    if (this.selectedAccount === undefined || this.selectedAccount === this.appService.DUMMY_BANK_ACCOUNT) {
      console.error('Selected account number is undefined or dummy in handleAccountChange');
      return;
    }

    this.transactionQuery  = {
      transactionType: TransactionTypeEnum.BOTH,
      counterpartyName: undefined,
      minAmount: undefined,
      maxAmount: undefined,
      accountNumber: this.selectedAccount,
      categoryId: undefined,
      counterpartyAccountNumber: undefined,
      startDate: undefined,
      endDate: undefined,
      transactionOrCommunication: undefined,
      uploadTimestamp: undefined
    }

    this.doQuery(this.transactionQuery);
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
      (request:any, query:any) => {
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
    let category = this.categoryMap?.getSimpleCategory(selectedCategoryQualifiedNameStr);
    if (!category) {
      throw new Error("No category found for " + selectedCategoryQualifiedNameStr);
    }
    transaction.category = category;
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
      (request:any, query: any) => {
        return this.appService.pageTransactions(request, query);
      },
      newSort, transactionQuery
    );

    this.viewType = ViewType.RUN_QUERY;
  }



  getNrOfTransactionsToManuallyReview(): string {
    if (this.transactionToManuallyReview !== undefined && this.transactionToManuallyReview !== null){
      return this.transactionToManuallyReview.toString();
    }
    return "";
  }

  getNrOfTransactionsToManuallyReviewTooltip(): string {
    if (this.transactionToManuallyReview !== undefined && this.transactionToManuallyReview !== null){
      return `You have ${this.transactionToManuallyReview} transactions to manually review`;
    }
    return "";
  }
}
