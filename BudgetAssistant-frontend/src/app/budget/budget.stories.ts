import type { Meta, StoryObj } from '@storybook/angular';
import { moduleMetadata } from '@storybook/angular';
import { BudgetComponent } from './budget.component';
import { ReactiveFormsModule } from '@angular/forms';
import { BehaviorSubject, of } from 'rxjs';
import { AppService } from '../app.service';
import { BankAccount } from '@daanvdn/budget-assistant-client';
import { MatTreeModule } from '@angular/material/tree';
import { MatTableModule } from '@angular/material/table';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatDialogModule } from '@angular/material/dialog';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { BankAccountSelectionComponent } from '../bank-account-selection/bank-account-selection.component';
import { IbanPipe } from '../iban.pipe';

// Mock BankAccount data
const mockBankAccounts: BankAccount[] = [
  { accountNumber: 'NL91ABNA0417164300', alias: 'Main Account', users: [1] },
  { accountNumber: 'NL39RABO0300065264', alias: 'Savings', users: [1] }
];

// Mock Budget Tree Nodes
const mockBudgetTreeNodes = [
  {
    budgetTreeNodeAmount: 1000,
    budgetTreeNodeId: 1,
    budgetTreeNodeParentId: 0,
    children: [
      {
        budgetTreeNodeAmount: 400,
        budgetTreeNodeId: 2,
        budgetTreeNodeParentId: 1,
        children: [],
        name: 'Groceries',
        qualifiedName: 'Household Expenses:Groceries'
      },
      {
        budgetTreeNodeAmount: 350,
        budgetTreeNodeId: 3,
        budgetTreeNodeParentId: 1,
        children: [],
        name: 'Utilities',
        qualifiedName: 'Household Expenses:Utilities'
      }
    ],
    name: 'Household Expenses',
    qualifiedName: 'Household Expenses'
  },
  {
    budgetTreeNodeAmount: 500,
    budgetTreeNodeId: 4,
    budgetTreeNodeParentId: 0,
    children: [
      {
        budgetTreeNodeAmount: 200,
        budgetTreeNodeId: 5,
        budgetTreeNodeParentId: 4,
        children: [],
        name: 'Dining Out',
        qualifiedName: 'Leisure:Dining Out'
      },
      {
        budgetTreeNodeAmount: 150,
        budgetTreeNodeId: 6,
        budgetTreeNodeParentId: 4,
        children: [],
        name: 'Entertainment',
        qualifiedName: 'Leisure:Entertainment'
      }
    ],
    name: 'Leisure',
    qualifiedName: 'Leisure'
  }
];

// Mock AppService
const mockAppService = {
  fetchBankAccountsForUser: () => new BehaviorSubject(mockBankAccounts),
  selectedBankAccountObservable$: new BehaviorSubject(mockBankAccounts[0]),
  findOrCreateBudget: () => of(mockBudgetTreeNodes),
  updateBudgetEntryAmount: () => of({ response: 'success', failureReason: null, errorMessage: null }),
  setBankAccount: () => {}
};

const meta: Meta<BudgetComponent> = {
  title: 'Components/Budget',
  component: BudgetComponent,
  decorators: [
    moduleMetadata({
      imports: [
        ReactiveFormsModule,
        MatTreeModule,
        MatTableModule,
        MatFormFieldModule,
        MatInputModule,
        MatButtonModule,
        MatIconModule,
        MatToolbarModule,
        MatDialogModule,
        NoopAnimationsModule,
        BankAccountSelectionComponent,
        IbanPipe
      ],
      providers: [
        { provide: AppService, useValue: mockAppService }
      ],
    }),
  ],
  parameters: {
    layout: 'fullscreen',
  },
};

export default meta;
type Story = StoryObj<BudgetComponent>;

export const Default: Story = {
  args: {},
};

export const EmptyBudget: Story = {
  args: {},
  decorators: [
    moduleMetadata({
      providers: [
        {
          provide: AppService,
          useValue: {
            fetchBankAccountsForUser: () => new BehaviorSubject(mockBankAccounts),
            selectedBankAccountObservable$: new BehaviorSubject(mockBankAccounts[0]),
            findOrCreateBudget: () => of([]),
            updateBudgetEntryAmount: () => of({ response: 'success', failureReason: null, errorMessage: null }),
            setBankAccount: () => {}
          }
        }
      ],
    }),
  ],
};

const errorNode = {
  budgetTreeNodeAmount: 200, // Parent amount less than sum of children (300)
  budgetTreeNodeId: 10,
  budgetTreeNodeParentId: 0,
  children: [
    {
      budgetTreeNodeAmount: 150,
      budgetTreeNodeId: 11,
      budgetTreeNodeParentId: 10,
      children: [],
      name: 'Child 1',
      qualifiedName: 'Error Category:Child 1'
    },
    {
      budgetTreeNodeAmount: 150,
      budgetTreeNodeId: 12,
      budgetTreeNodeParentId: 10,
      children: [],
      name: 'Child 2',
      qualifiedName: 'Error Category:Child 2'
    }
  ],
  name: 'Error Category',
  qualifiedName: 'Error Category'
}
let dataForErrorState = mockBudgetTreeNodes.concat([errorNode]);

export const WithErrorState: Story = {
  args: {},
  decorators: [
    moduleMetadata({
      providers: [
        {
          provide: AppService,
          useValue: {
            fetchBankAccountsForUser: () => new BehaviorSubject(mockBankAccounts),
            selectedBankAccountObservable$: new BehaviorSubject(mockBankAccounts[0]),
            findOrCreateBudget: () => of(dataForErrorState),
            updateBudgetEntryAmount: () => of({ response: 'success', failureReason: null, errorMessage: null }),
            setBankAccount: () => {}
          }
        }
      ],
    }),
  ],

};