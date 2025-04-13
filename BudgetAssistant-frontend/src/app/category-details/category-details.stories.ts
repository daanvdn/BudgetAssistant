import type {Meta, StoryObj} from '@storybook/angular';
import {moduleMetadata} from '@storybook/angular';
import {CategoryDetailsComponent} from './category-details.component';
import {MatListModule} from '@angular/material/list';
import {ChartModule} from 'primeng/chart';
import {NgFor, NgIf} from '@angular/common';
import {BankAccount, GroupingEnum, TransactionTypeEnum} from '@daanvdn/budget-assistant-client';
import {Criteria} from '../model/criteria.model';
import {AppService} from '../app.service';

// Mock BankAccount data
const mockBankAccount: BankAccount = {
  accountNumber: '123456789',
  alias: 'Main Account',
  users: [1]
};

// Mock Criteria
const mockExpensesCriteria = new Criteria(
  mockBankAccount,
    GroupingEnum.month,
  new Date('2025-01-01'),
  new Date('2025-12-31'),
    TransactionTypeEnum.EXPENSES
);
const mockRevenueCriteria = new Criteria(
  mockBankAccount,
    GroupingEnum.month,
  new Date('2025-01-01'),
  new Date('2025-12-31'),
    TransactionTypeEnum.REVENUE
);



const meta: Meta<CategoryDetailsComponent> = {
  title: 'Components/CategoryDetails',
  component: CategoryDetailsComponent,
  decorators: [
    moduleMetadata({
      imports: [MatListModule, ChartModule, NgIf, NgFor],
      providers: [
        { 
          provide: AppService, 
          useValue: {
            selectedBankAccountObservable$: { subscribe: () => {} },
            getCategoriesForAccountAndTransactionType: () => ({ subscribe: () => {} }),
            getCategoryDetailsForPeriod: () => ({ subscribe: () => {} })
          } 
        }
      ],
    }),
  ],
  parameters: {
    layout: 'fullscreen',
  },
};

export default meta;
type Story = StoryObj<CategoryDetailsComponent>;

export const ExpensesView: Story = {
  args: {
    criteria: mockExpensesCriteria,
    expensesCategories: [
      { name: 'Groceries', transactionType: TransactionTypeEnum.EXPENSES },
      { name: 'Utilities', transactionType: TransactionTypeEnum.EXPENSES },
    ],
    revenueCategories: [
      { name: 'Salary', transactionType: TransactionTypeEnum.REVENUE },
      { name: 'Investments', transactionType: TransactionTypeEnum.REVENUE },
    ],
    datatIsLoaded: false,
    chartData: {
      labels: ['January', 'February', 'March'],
      datasets: [
        {
          label: 'Groceries',
          data: [200, 150, 180],
          backgroundColor: 'rgba(255, 99, 132, 0.2)',
          borderColor: 'rgba(255, 99, 132, 1)',
          borderWidth: 1,
        },
        {
          label: 'Utilities',
          data: [100, 120, 130],
          backgroundColor: 'rgba(54, 162, 235, 0.2)',
          borderColor: 'rgba(54, 162, 235, 1)',
          borderWidth: 1,
        }

      ],
    },
    chartOptions: {
      responsive: true,
      scales: {
        x: { stacked: true },
        y: { stacked: true },
      },
    },
  }
};


export const RevenueView: Story = {
  args: {
    ...ExpensesView.args,
    criteria: mockRevenueCriteria,
  }
};

