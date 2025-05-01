import * as Factory from "factory.ts";
import type { Meta, StoryObj } from '@storybook/angular';
import { moduleMetadata } from '@storybook/angular';
import { TransactionsComponent } from './transactions.component';
import { AppService } from '../app.service';
import { AuthService } from '../auth/auth.service';
import { ErrorDialogService } from '../error-dialog/error-dialog.service';
import { DateUtilsService } from '../shared/date-utils.service';
import { BehaviorSubject, Observable, of } from 'rxjs';
import { Counterparty, CategoryMap, AmountType } from '../model';
import { BankAccountSelectionComponent } from '../bank-account-selection/bank-account-selection.component';
import { MatDialogModule } from '@angular/material/dialog';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatBadgeModule } from '@angular/material/badge';
import { MatTableModule } from '@angular/material/table';
import { MatSortModule } from '@angular/material/sort';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatRadioModule } from '@angular/material/radio';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { DatePipe, NgIf, AsyncPipe, TitleCasePipe } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import { CategoryTreeDropdownComponent } from '../category-tree-dropdown/category-tree-dropdown.component';
import {Page, PageRequest, PaginationDataSource} from 'ngx-pagination-data-source';
import { HttpEventType } from '@angular/common/http';
import {BankAccount, SimpleCategory, SimplifiedCategory, Transaction, TransactionTypeEnum, TypeEnum} from '@daanvdn/budget-assistant-client';

// Define ViewType enum to match the one in the component
enum ViewType {
  INITIAL_VIEW = "INITIAL_VIEW",
  RUN_QUERY = "RUN_QUERY",
  SHOW_ALL = "SHOW_ALL",
  UPLOAD_TRANSACTIONS = "UPLOAD_TRANSACTIONS",
}

// Mock data
const mockCounterparty: Counterparty = {
  name: 'Test Counterparty',
  accountNumber: 'NL91ABNA0417164300',
  streetAndNumber: '123 Test Street',
  zipCodeAndCity: '1234 AB Test City',
  category: null
};

const mockCategory: SimpleCategory  = {
  qualifiedName: "Category A",
  name: "Category A",
  id: 0
}

// Mock SimplifiedCategory data for category tree
const mockSimplifiedCategories: SimplifiedCategory[] = [
  {
    children: [],
    name: "Expenses",
    qualifiedName: "Expenses",
    type: "EXPENSES" as TypeEnum,
    id: 1
  },
  {
    children: [],
    name: "Revenue",
    qualifiedName: "Revenue",
    type: "REVENUE" as TypeEnum,
    id: 2
  }
];

//create 50 mock transactions using factory.ts
const mockTransactionFactory = Factory.Sync.makeFactory<Transaction>({
  transactionId: Factory.each(i => `${i}`),
  bankAccount: 'NL91ABNA0417164300',
  bookingDate: (new Date()).toDateString(),
  statementNumber: '001',
  transactionNumber: Factory.each(i => `${i}`),
  counterparty: {
    name: "Test Counterparty",
    accountNumber: 'BE95ABNA0417164300',
  },
  transaction: Factory.each(i => `Test Transaction ${i}`),
  currencyDate: (new Date()).toDateString(),
  amount: Factory.each(i => i * 10),
  currency: 'EUR',
  bic: 'ABNANL2A',
  countryCode: 'NL',
  communications: Factory.each(i => `Test Communication ${i}`),
  category: mockCategory,
  manuallyAssignedCategory: false,
  isRecurring: false,
  isAdvanceSharedAccount: false,
  isManuallyReviewed: true
});
const mockTransactionsLarge: Transaction[] = mockTransactionFactory.buildList(50);

const mockBankAccounts: BankAccount[] = [
  { accountNumber: 'NL91ABNA0417164300', alias: 'Main Account', users: [1] },
  { accountNumber: 'NL39RABO0300065264', alias: 'Savings', users: [1] }
];

//create mock pages for transactionsLarge. Each of size 10
const mockPages: Page<Transaction>[] = [];
for (let i = 0; i < mockTransactionsLarge.length / 10; i++) {
  mockPages.push({
    content: mockTransactionsLarge.slice(i * 10, (i + 1) * 10),
    number: i,
    size: 10,
    totalElements: mockTransactionsLarge.length
  });
}

// Mock page result for PaginationDataSource
const mockPage: Page<Transaction> = {
  content: mockTransactionsLarge,
  number: 0,
  size: 10,
  totalElements: mockTransactionsLarge.length,
};

// Mock services
const mockAppService = {
  pageTransactions: (request: PageRequest<Transaction>, query: any): Observable<Page<Transaction>> => {
    // Get the page index from the request, default to 0 if not provided
    const pageIndex = request?.page || 0;
    console.log('pageTransactions called with pageIndex:', pageIndex);
    // Return the appropriate page from mockPages
    if (pageIndex >= 0 && pageIndex < mockPages.length) {
      let currentPage: Page<Transaction> = mockPages[pageIndex];
      console.log('Returning page:', currentPage);
      return of(currentPage);
    }
    // Fallback to the first page if the requested page doesn't exist
    console.log('Page index out of range, returning first page');
    return of(mockPages[0]);
  },
  saveTransaction: () => {},
  uploadTransactionFiles: () => of({ type: HttpEventType.Response, body: { uploadTimestamp: '2023-01-01' } }),
  countTransactionToManuallyReview: () => of(2),
  categoryMapObservable$: new BehaviorSubject<CategoryMap | undefined>(undefined),
  selectedBankAccountObservable$: new BehaviorSubject<BankAccount | undefined>(mockBankAccounts[0]),
  DUMMY_BANK_ACCOUNT: 'DUMMY',
  fetchBankAccountsForUser: () => new BehaviorSubject(mockBankAccounts),
  setBankAccount: () => {},
  // Add missing observables for CategoryTreeDropdownComponent
  sharedCategoryTreeRevenueObservable$: of(mockSimplifiedCategories.filter(cat => cat.type === "REVENUE" as TypeEnum)),
  sharedCategoryTreeExpensesObservable$: of(mockSimplifiedCategories.filter(cat => cat.type === "EXPENSES" as TypeEnum)),
  sharedCategoryTreeObservable$: of(mockSimplifiedCategories)
};

const mockAuthService = {
  getUser: () => ({ userName: 'testuser' })
};

const mockErrorDialogService = {
  openErrorDialog: () => {}
};

const mockDateUtilsService = {
  parseDate: (dateStr: string | undefined | null) => dateStr ? new Date(dateStr) : null
};

// Mock components
const mockBankAccountSelectionComponent = {
  selector: 'bank-account-selection',
  template: '<div>Bank Account Selection Mock</div>',
  inputs: ['selectedBankAccount'],
  outputs: ['change']
};

const mockCategoryTreeDropdownComponent = {
  selector: 'app-category-tree-dropdown',
  template: '<div>Category Tree Dropdown Mock</div>',
  inputs: ['selectedCategoryQualifiedNameStr', 'transactionTypeEnum'],
  outputs: ['selectionChange']
};

const meta: Meta<TransactionsComponent> = {
  title: 'Components/TransactionsComponent',
  component: TransactionsComponent,
  decorators: [
    moduleMetadata({
      imports: [
        NoopAnimationsModule,
        MatToolbarModule,
        MatProgressSpinnerModule,
        MatButtonModule,
        MatIconModule,
        MatTooltipModule,
        MatBadgeModule,
        MatTableModule,
        MatSortModule,
        MatPaginatorModule,
        MatRadioModule,
        MatDialogModule,
        RouterModule.forChild([]),
        NgIf,
        AsyncPipe,
        TitleCasePipe,
        BankAccountSelectionComponent,
        CategoryTreeDropdownComponent,
        FaIconComponent
      ],
      declarations: [],
      providers: [
        { provide: AppService, useValue: mockAppService },
        { provide: AuthService, useValue: mockAuthService },
        { provide: ErrorDialogService, useValue: mockErrorDialogService },
        { provide: DateUtilsService, useValue: mockDateUtilsService },
        { provide: DatePipe, useClass: DatePipe }
      ]
    })
  ],
  parameters: {
    layout: 'fullscreen',
  }
};

export default meta;
type Story = StoryObj<TransactionsComponent>;

// Create a mock PaginationDataSource
const createMockDataSource = () => {
  const dataSource = new PaginationDataSource<Transaction, any>(
    (request: PageRequest<Transaction>, query: any) => mockAppService.pageTransactions(request, query),
    { property: 'bookingDate', order: 'desc' },
    {}
  );

  // Override the fetch method to ensure it correctly handles page changes
  const originalFetch = dataSource.fetch;
  dataSource.fetch = (pageIndex: number) => {
    console.log('dataSource.fetch called with pageIndex:', pageIndex);
    return originalFetch.call(dataSource, pageIndex);
  };

  return dataSource;
};

// Basic story
export const Default: Story = {
  args: {},
  render: (args) => {
    const dataSource = createMockDataSource();
    return {
      props: {
        ...args,
        dataSource: dataSource,
        viewType: ViewType.SHOW_ALL,
        amountType: () => AmountType.BOTH,
        parseDate: (dateStr: string) => new Date(dateStr)
      },
      template: `
        <app-transactions [dataSource]="dataSource" [viewType]="viewType"></app-transactions>
      `
    };
  }
};

// Story with transactions being uploaded
export const UploadingFiles: Story = {
  args: {},
  render: (args) => {
    const dataSource = createMockDataSource();
    return {
      props: {
        ...args,
        dataSource: dataSource,
        viewType: ViewType.UPLOAD_TRANSACTIONS,
        filesAreUploading: true,
        amountType: () => AmountType.BOTH,
        parseDate: (dateStr: string) => new Date(dateStr)
      },
      template: `
        <app-transactions [dataSource]="dataSource" [viewType]="viewType" [filesAreUploading]="filesAreUploading"></app-transactions>
      `
    };
  }
};

// Story showing search results
export const SearchResults: Story = {
  args: {},
  render: (args) => {
    const dataSource = createMockDataSource();
    return {
      props: {
        ...args,
        dataSource: dataSource,
        viewType: ViewType.RUN_QUERY,
        amountType: () => AmountType.BOTH,
        parseDate: (dateStr: string) => new Date(dateStr)
      },
      template: `
        <app-transactions [dataSource]="dataSource" [viewType]="viewType"></app-transactions>
      `
    };
  }
};
