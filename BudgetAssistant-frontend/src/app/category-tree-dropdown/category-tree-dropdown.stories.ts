import type { Meta, StoryObj } from '@storybook/angular';
import { moduleMetadata } from '@storybook/angular';
import { CategoryTreeDropdownComponent, BackingDatabase } from './category-tree-dropdown.component';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { FormsModule, ReactiveFormsModule, FormBuilder } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { MatTreeModule } from '@angular/material/tree';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { BehaviorSubject } from 'rxjs';
import { TransactionTypeEnum, SimplifiedCategory } from '@daanvdn/budget-assistant-client';
import { FlatCategoryNode, NO_CATEGORY } from '../model';
import { AppService } from '../app.service';

// Mock SimplifiedCategory data
const createMockCategory = (
  id: number,
  name: string,
  qualifiedName: string,
  type: TransactionTypeEnum,
  children: Array<{ [key: string]: any }> = []
): SimplifiedCategory => ({
  id,
  name,
  qualifiedName,
  type,
  children
});

// Create mock category hierarchies
const mockExpensesCategories: SimplifiedCategory[] = [
  createMockCategory(1, 'Housing', 'Housing', TransactionTypeEnum.EXPENSES, [
    { 'Rent': createMockCategory(2, 'Rent', 'Housing.Rent', TransactionTypeEnum.EXPENSES) },
    { 'Utilities': createMockCategory(3, 'Utilities', 'Housing.Utilities', TransactionTypeEnum.EXPENSES, [
      { 'Electricity': createMockCategory(4, 'Electricity', 'Housing.Utilities.Electricity', TransactionTypeEnum.EXPENSES) },
      { 'Water': createMockCategory(5, 'Water', 'Housing.Utilities.Water', TransactionTypeEnum.EXPENSES) }
    ]) }
  ]),
  createMockCategory(6, 'Food', 'Food', TransactionTypeEnum.EXPENSES, [
    { 'Groceries': createMockCategory(7, 'Groceries', 'Food.Groceries', TransactionTypeEnum.EXPENSES) },
    { 'Dining Out': createMockCategory(8, 'Dining Out', 'Food.Dining Out', TransactionTypeEnum.EXPENSES) }
  ])
];

const mockRevenueCategories: SimplifiedCategory[] = [
  createMockCategory(9, 'Income', 'Income', TransactionTypeEnum.REVENUE, [
    { 'Salary': createMockCategory(10, 'Salary', 'Income.Salary', TransactionTypeEnum.REVENUE) },
    { 'Bonus': createMockCategory(11, 'Bonus', 'Income.Bonus', TransactionTypeEnum.REVENUE) }
  ]),
  createMockCategory(12, 'Investments', 'Investments', TransactionTypeEnum.REVENUE, [
    { 'Dividends': createMockCategory(13, 'Dividends', 'Investments.Dividends', TransactionTypeEnum.REVENUE) },
    { 'Interest': createMockCategory(14, 'Interest', 'Investments.Interest', TransactionTypeEnum.REVENUE) }
  ])
];

// Mock AppService
const mockAppService = {
  sharedCategoryTreeExpensesObservable$: new BehaviorSubject<SimplifiedCategory[]>(mockExpensesCategories),
  sharedCategoryTreeRevenueObservable$: new BehaviorSubject<SimplifiedCategory[]>(mockRevenueCategories),
  sharedCategoryTreeObservable$: new BehaviorSubject<SimplifiedCategory[]>([...mockExpensesCategories, ...mockRevenueCategories])
};

const meta: Meta<CategoryTreeDropdownComponent> = {
  title: 'Components/CategoryTreeDropdown',
  component: CategoryTreeDropdownComponent,
  decorators: [
    moduleMetadata({
      imports: [
        BrowserAnimationsModule,
        FormsModule,
        ReactiveFormsModule,
        MatFormFieldModule,
        MatInputModule,
        MatAutocompleteModule,
        MatTreeModule,
        MatCheckboxModule,
        MatIconModule,
        MatButtonModule
      ],
      providers: [
        FormBuilder,
        { provide: AppService, useValue: mockAppService }
      ],
    }),
  ],
  parameters: {
    layout: 'centered',
  },
};

export default meta;
type Story = StoryObj<CategoryTreeDropdownComponent>;

// Default story with expenses categories
export const ExpensesCategories: Story = {
  args: {
    transactionTypeEnum: TransactionTypeEnum.EXPENSES
  }
};

// Story with revenue categories
export const RevenueCategories: Story = {
  args: {
    transactionTypeEnum: TransactionTypeEnum.REVENUE
  }
};

// Story with both category types
export const AllCategories: Story = {
  args: {
    transactionTypeEnum: TransactionTypeEnum.BOTH
  }
};

// Story with preselected category
export const WithPreselectedCategory: Story = {
  args: {
    transactionTypeEnum: TransactionTypeEnum.EXPENSES,
    selectedCategoryQualifiedNameStr: 'Housing.Utilities.Electricity'
  }
};