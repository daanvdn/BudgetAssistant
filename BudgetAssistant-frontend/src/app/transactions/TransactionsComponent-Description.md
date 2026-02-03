# TransactionsComponent Comprehensive Description

## Overview

The `TransactionsComponent` is an Angular standalone component that serves as the primary interface for viewing, managing, and searching financial transactions. It displays transactions in a paginated Material Design table with sorting capabilities, allows users to upload CSV transaction files, search/filter transactions, and categorize individual transactions.

---

## TypeScript Component (`transactions.component.ts`)

### Location
`BudgetAssistant-frontend/src/app/transactions/transactions.component.ts`

### Component Metadata
```typescript
@Component({
    selector: 'app-transactions',
    templateUrl: './transactions.component.html',
    styleUrls: ['./transactions.component.scss'],
    standalone: true,
    imports: [/* see imports below */]
})
```

### Imports from Angular Material & Other Libraries
- **Layout & Containers**: `MatToolbar`, `MatTable`, `MatCell`, `MatHeaderCell`, `MatRow`, `MatHeaderRow`, etc.
- **Pagination**: `MatPaginator`
- **Sorting**: `MatSort`, `MatSortHeader`
- **Forms**: `MatRadioGroup`, `MatRadioButton`
- **UI Elements**: `MatButton`, `MatIcon`, `MatTooltip`, `MatBadge`, `MatProgressSpinner`
- **Dialog**: `MatDialog`
- **Pipes**: `AsyncPipe`, `TitleCasePipe`, `DatePipe`, `NgIf`
- **FontAwesome**: `FaIconComponent`, `faTag`
- **Third-party**: `PaginationDataSource` from `ngx-pagination-data-source`

### Imports from New API Client (`@daanvdn/budget-assistant-client`)
- `TransactionRead` - The transaction data model for reading
- `TransactionQuery` - Query parameters for filtering transactions
- `TransactionTypeEnum` - Enum with values: `EXPENSES`, `REVENUE`, `BOTH`

### Component State

#### View Types (Enum)
```typescript
enum ViewType {
    INITIAL_VIEW = "INITIAL_VIEW",    // Default state before any action
    RUN_QUERY = "RUN_QUERY",          // Search results being displayed
    SHOW_ALL = "SHOW_ALL",            // All transactions displayed
    UPLOAD_TRANSACTIONS = "UPLOAD_TRANSACTIONS", // Recently uploaded transactions displayed
}
```

#### Properties
| Property | Type | Description |
|----------|------|-------------|
| `paginator` | `MatPaginator` | ViewChild for pagination control |
| `sort` | `MatSort` | ViewChild for sorting control |
| `table` | `MatTable<TransactionRead>` | ViewChild for the material table |
| `accountSelectionComponent` | `BankAccountSelectionComponent` | ViewChild for bank account dropdown |
| `currentSort` | `any` | Current sorting configuration |
| `filesAreUploading` | `boolean` | Flag to show upload overlay spinner |
| `transactionToManuallyReview` | `number` | Count of transactions requiring manual review |
| `dataSource` | `PaginationDataSource<TransactionRead, TransactionQuery>` | Paginated data source for the table (can be `@Input()`) |
| `displayedColumns` | `string[]` | Table columns: `["bookingDate", "counterparty", "transaction", "amount", "transactionType"]` |
| `transactionQuery` | `TransactionQuery` | Current active query filter |
| `transactionQueryAsJson` | `string` | JSON representation of current query (for debugging) |
| `selectedAccount` | `string` | Currently selected bank account number |
| `fileInput` | `any` | ViewChild reference to hidden file input |
| `viewType` | `ViewType` | Current view state |
| `categoryMap` | `CategoryMap` | Map for category ID/name lookups |

### Dependencies (Injected Services)
| Service | Purpose |
|---------|---------|
| `AppService` | Main application service for API calls and state management |
| `AuthService` | Authentication and user information |
| `MatDialog` | Material dialog service for opening search dialog |
| `DatePipe` | Angular date formatting pipe |
| `ErrorDialogService` | Displaying error dialogs |
| `Router` | Angular router for navigation |
| `DateUtilsService` | Date parsing utilities |

### Constructor Logic
1. Initializes `dataSource` with `initDataSource()` if not provided via `@Input()`
2. Subscribes to `appService.categoryMapObservable$` to keep `categoryMap` updated
3. Subscribes to `appService.selectedBankAccountObservable$` to update `transactionToManuallyReview` count when bank account changes

### Key Methods

#### File Upload
| Method | Description |
|--------|-------------|
| `onClickFileInputButton()` | Triggers hidden file input click |
| `onChangeFileInput()` | Handles file selection, uploads CSV files via `appService.uploadTransactionFiles()`, then displays uploaded transactions |

#### Navigation & Dialogs
| Method | Description |
|--------|-------------|
| `showTransactionsToManuallyReview()` | Navigates to `/categorieën` route if there are transactions to review |
| `openDialog()` | Opens `TransactionSearchDialogComponent` and executes query on close |

#### Query & Display
| Method | Description |
|--------|-------------|
| `handleAccountChange()` | Called when bank account selection changes; creates new query with account filter |
| `showAllTransactions()` | Resets to show all transactions for selected account |
| `doQuery(transactionQuery)` | Executes a transaction query and updates the dataSource |
| `initDataSource(account)` | Creates a new `PaginationDataSource` with optional account filter |

#### Transaction Editing
| Method | Description |
|--------|-------------|
| `saveTransaction(transaction)` | Saves transaction changes via `appService.saveTransaction()` |
| `setIsRecurring(transaction, event)` | Sets `isRecurring` flag on transaction |
| `setIsAdvanceSharedAccount(transaction, event)` | Sets `isAdvanceSharedAccount` flag on transaction |
| `setCategory(transaction, selectedCategoryQualifiedNameStr)` | Sets category on transaction by looking up category ID from `categoryMap` |

#### Sorting
| Method | Description |
|--------|-------------|
| `sortBy(event)` | Handles sort change events from MatSort |

#### Display Helpers
| Method | Description |
|--------|-------------|
| `translateBooleanToDutchJaNee(b)` | Converts boolean to Dutch "ja"/"nee" |
| `displayNumberOrNA(number)` | Returns number as string or "N/A" |
| `displayStringOrNA(s)` | Returns string or "N/A" |
| `displayDateOrNA(s)` | Formats date or returns "N/A" |
| `parseDate(dateStr)` | Delegates to `DateUtilsService.parseDate()` |
| `amountType(transaction)` | Infers `AmountType` (REVENUE/EXPENSES/BOTH) from transaction amount |
| `getNrOfTransactionsToManuallyReview()` | Returns badge count string |
| `getNrOfTransactionsToManuallyReviewTooltip()` | Returns tooltip text for review count |

---

## HTML Template (`transactions.component.html`)

### Location
`BudgetAssistant-frontend/src/app/transactions/transactions.component.html`

### Structure Overview

```
┌─────────────────────────────────────────────────────────────────┐
│ MatToolbar (header: "Transactions")                             │
├─────────────────────────────────────────────────────────────────┤
│ Upload Overlay (shown when filesAreUploading)                   │
│   - MatSpinner with "Bestanden worden geüpload" message         │
├─────────────────────────────────────────────────────────────────┤
│ Toolbar Row:                                                    │
│   - BankAccountSelectionComponent                               │
│   - Upload button (add_to_photos icon)                          │
│   - Search button (search icon) -> opens dialog                 │
│   - Show all button (remove_red_eye icon)                       │
│   - Manual review button (faTag icon with badge)                │
│   - View type indicator (conditional text)                      │
│   - MatPaginator (top)                                          │
├─────────────────────────────────────────────────────────────────┤
│ Transaction Table (MatTable with MatSort):                      │
│   Columns:                                                      │
│   1. bookingDate - Date column with sort                        │
│   2. counterparty - Name, account number, address (NESTED OBJ)  │
│   3. transaction - Transaction description + communications     │
│   4. amount - Amount with currency                              │
│   5. transactionType - Category dropdown, recurring radio,      │
│                        reimbursement radio                      │
├─────────────────────────────────────────────────────────────────┤
│ MatPaginator (bottom)                                           │
└─────────────────────────────────────────────────────────────────┘
```

### Template Details

#### Header & Upload Overlay
- Fixed toolbar with "Transactions" title
- Overlay with spinner shown when `filesAreUploading` is true

#### Action Buttons Row
1. **Bank Account Selection**: `<bank-account-selection>` component with `(change)="handleAccountChange()"`
2. **Upload CSV Button**: Hidden file input triggered by button click
3. **Search Button**: Opens `TransactionSearchDialogComponent`
4. **Show All Button**: Calls `showAllTransactions()`
5. **Manual Review Badge Button**: Shows count badge, navigates to `/categorieën` on click

#### View Type Indicators
- Conditional `*ngIf` templates showing:
  - "Zoekresultaten worden getoond" for `RUN_QUERY`
  - "Alle records worden getoond" for `SHOW_ALL`
  - "Records van geüploade bestanden" for `UPLOAD_TRANSACTIONS`

#### Transaction Table

##### Column: `bookingDate`
```html
<td mat-cell *matCellDef="let item">
    {{ parseDate(item.bookingDate) | date: 'dd/MM/yyyy' }}
</td>
```

##### Column: `counterparty` ⚠️ **PROBLEM AREA**
```html
<td mat-cell *matCellDef="let item">
    <div>{{ item.counterparty.name | titlecase }}</div>
    <div>{{ item.counterparty.accountNumber }}</div>
    <div>{{ item.counterparty.streetAndNumber }} {{ item.counterparty.zipCodeAndCity }}</div>
</td>
```
**Issue**: The template accesses `item.counterparty.name`, `item.counterparty.accountNumber`, etc., but the **new API client's `TransactionRead` model does NOT have a nested `counterparty` object**. Instead, it only has a `counterpartyId: string` field. The old API model had a nested `Counterparty` object with `name`, `accountNumber`, `streetAndNumber`, and `zipCodeAndCity` properties.

##### Column: `transaction`
```html
<td mat-cell *matCellDef="let item">
    <div>{{ item.transaction }}</div>
    <div *ngIf="item.transaction !== item.communications">{{ item.communications }}</div>
</td>
```

##### Column: `amount`
```html
<td mat-cell *matCellDef="let item">
    <div>{{ item.amount }} {{ item.currency }}</div>
</td>
```

##### Column: `transactionType`
This is a complex column with three sub-rows:

1. **Category Selection**:
```html
<app-category-tree-dropdown
    (selectionChange)="setCategory(item, $event)"
    [selectedCategoryQualifiedNameStr]="item.category"
    [transactionTypeEnum]="amountType(item)"
>
</app-category-tree-dropdown>
```
⚠️ **Issue**: Binds to `item.category` but new API uses `item.categoryId` (a number, not a category object/qualified name string).

2. **Recurring Radio Buttons**:
```html
<mat-radio-group (change)="setIsRecurring(item, $event)">
    <mat-radio-button [value]="true" [checked]="item.isRecurring == true">ja</mat-radio-button>
    <mat-radio-button [value]="false" [checked]="item.isRecurring == false">nee</mat-radio-button>
</mat-radio-group>
```

3. **Reimbursement Radio Buttons**:
```html
<mat-radio-group (change)="setIsAdvanceSharedAccount(item, $event)">
    <mat-radio-button [value]="true" [checked]="item.isAdvanceSharedAccount == true">ja</mat-radio-button>
    <mat-radio-button [value]="false" [checked]="item.isAdvanceSharedAccount == false">nee</mat-radio-button>
</mat-radio-group>
```

#### Pagination
Two `MatPaginator` instances (top and bottom) using async pipe:
```html
<mat-paginator *ngIf="dataSource.page$ | async as page" 
    [length]="page.totalElements" 
    [pageSize]="page.size"
    [pageIndex]="page.number" 
    (page)="dataSource.fetch($event.pageIndex)">
</mat-paginator>
```

---

## Component Dependencies (Child Components)

### 1. `BankAccountSelectionComponent`
- **Selector**: `bank-account-selection`
- **Location**: `src/app/bank-account-selection/`
- **Purpose**: Dropdown to select a bank account
- **Inputs/Outputs**: Emits `change` event with `BankAccountRead` when selection changes
- **Exposed Property**: `selectedBankAccount: BankAccountRead`

### 2. `CategoryTreeDropdownComponent`
- **Selector**: `app-category-tree-dropdown`
- **Location**: `src/app/category-tree-dropdown/`
- **Purpose**: Autocomplete dropdown with tree structure for selecting transaction categories
- **Inputs**:
  - `selectedCategoryQualifiedNameStr: string` - The currently selected category's qualified name
  - `transactionTypeEnum: AmountType` - Filter categories by REVENUE/EXPENSES/BOTH
- **Outputs**: `selectionChange` - Emits qualified name string when selection changes

### 3. `TransactionSearchDialogComponent`
- **Selector**: `app-transaction-search-dialog`
- **Location**: `src/app/transaction-search-dialog/`
- **Purpose**: Material dialog for building transaction search queries
- **Returns**: `TransactionQuery` object on close (or undefined if cancelled)
- **Contains**: Period selection, transaction type selection, category selection, counterparty filters, etc.

---

## Data Models

### New API Client Models (`@daanvdn/budget-assistant-client`)

#### `TransactionRead`
```typescript
interface TransactionRead { 
    transactionId: string;
    bankAccountId: string;           // Changed from bankAccount
    bookingDate: string;
    statementNumber: string;
    counterpartyId: string;          // Changed from nested Counterparty object
    transactionNumber: string;
    transaction?: string | null;
    currencyDate: string;
    amount: number;
    currency: string;
    bic?: string | null;
    countryCode: string;
    communications?: string | null;
    categoryId?: number | null;      // Changed from category: SimpleCategory
    manuallyAssignedCategory: boolean;
    isRecurring: boolean;
    isAdvanceSharedAccount: boolean;
    uploadTimestamp: string;
    isManuallyReviewed: boolean;
}
```

#### `TransactionQuery`
```typescript
interface TransactionQuery { 
    transactionType?: TransactionTypeEnum | null;
    counterpartyName?: string | null;
    minAmount?: number | null;
    maxAmount?: number | null;
    accountNumber?: string | null;
    categoryId?: number | null;
    transactionOrCommunication?: string | null;
    counterpartyAccountNumber?: string | null;
    startDate?: string | null;
    endDate?: string | null;
    uploadTimestamp?: string | null;
    manuallyAssignedCategory?: boolean;
}
```

### Old API Client Models (for reference)

#### `Transaction` (Old)
```typescript
interface Transaction { 
    transactionId: string;
    bankAccount?: string;
    bookingDate?: string;
    statementNumber?: string;
    counterparty: Counterparty;           // <-- NESTED OBJECT
    counterpartyId: string;
    transactionNumber?: string;
    transaction?: string | null;
    currencyDate: string;
    amount?: number;
    currency?: string;
    bic?: string | null;
    countryCode?: string;
    communications: string | null;
    category?: SimpleCategory | null;     // <-- OBJECT with id, name, qualifiedName
    manuallyAssignedCategory?: boolean | null;
    isRecurring?: boolean | null;
    isAdvanceSharedAccount?: boolean | null;
    uploadTimestamp?: string;
    isManuallyReviewed?: boolean | null;
}
```

#### `Counterparty` (Old)
```typescript
interface Counterparty { 
    name: string;
    accountNumber: string;
    streetAndNumber?: string | null;
    zipCodeAndCity?: string | null;
    category?: number | null;
    users?: Array<number | null>;
}
```

---

## Key Issues to Address in Regeneration

### 1. Counterparty Data
**Problem**: Template accesses `item.counterparty.name`, `item.counterparty.accountNumber`, etc.
**New API**: Only provides `counterpartyId: string`
**Solution Needed**: Either:
- Fetch counterparty details separately and enrich transaction data
- Add counterparty details to the `TransactionRead` model on the backend
- Create a joined/enriched transaction model

### 2. Category Data
**Problem**: Template binds `[selectedCategoryQualifiedNameStr]="item.category"` expecting a string (qualified name)
**New API**: Only provides `categoryId?: number | null`
**Current Workaround**: The component has a `categoryMap` that can look up category info by ID
**Solution Needed**: Resolve category qualified name from `categoryId` for display

### 3. Field Nullability Changes
Many fields in the old API were optional (`?`) that are now required in the new API:
- `bankAccountId` (was `bankAccount?`)
- `statementNumber` (was optional)
- `amount` (was optional)
- `currency` (was optional)
- `countryCode` (was optional)
- Boolean fields now have default values instead of being nullable

---

## Services Used

### `AppService` Methods Used
| Method | Purpose |
|--------|---------|
| `categoryMapObservable$` | Observable of CategoryMap for category lookups |
| `selectedBankAccountObservable$` | Observable of currently selected bank account |
| `countTransactionToManuallyReview(accountNumber)` | Returns count of transactions needing review |
| `uploadTransactionFiles(fileWrappers, userName)` | Uploads CSV files |
| `triggerRefreshBankAccounts()` | Signals bank accounts should be refreshed |
| `pageTransactions(request, query)` | Paginated transaction fetching |
| `saveTransaction(transaction)` | Saves transaction updates |
| `DUMMY_BANK_ACCOUNT` | Constant for dummy/placeholder account |

### `AuthService` Methods Used
| Method | Purpose |
|--------|---------|
| `getUser()` | Returns current authenticated user |

---

## Summary

The `TransactionsComponent` is a feature-rich component for transaction management that:
1. Displays transactions in a sortable, paginated table
2. Allows CSV file uploads for importing transactions
3. Provides search/filter functionality via a dialog
4. Enables inline editing of transaction properties (category, recurring, reimbursement flags)
5. Shows a badge for transactions requiring manual review

**Critical Migration Issues**:
- The template expects nested `counterparty` object (old API) but new API only has `counterpartyId`
- The template expects `category` as a string/object but new API only has `categoryId`
- These issues will cause runtime errors until the template is updated to work with the new data model
