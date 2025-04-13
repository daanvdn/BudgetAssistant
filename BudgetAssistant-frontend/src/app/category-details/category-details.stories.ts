import type { Meta, StoryObj } from '@storybook/angular';
import { moduleMetadata } from '@storybook/angular';
import { CategoryDetailsComponent } from './category-details.component';
import { MatListModule } from '@angular/material/list';
import { ChartModule } from 'primeng/chart';
import { NgIf, NgFor } from '@angular/common';
import {TransactionTypeEnum} from '@daanvdn/budget-assistant-client';
import {GroupingEnum} from '@daanvdn/budget-assistant-client';
import { BankAccount} from '@daanvdn/budget-assistant-client';
import { Criteria } from '../model/criteria.model';
import { AppService } from '../app.service';

// Mock BankAccount data
const mockBankAccount: BankAccount = {
  accountNumber: '123456789',
  alias: 'Main Account',
  users: [1]
};

console.log(TransactionTypeEnum.EXPENSES)
// Mock Criteria
const mockCriteria = new Criteria(
  mockBankAccount,
    GroupingEnum.month,
  new Date('2025-01-01'),
  new Date('2025-12-31'),
    TransactionTypeEnum.EXPENSES
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

export const Default: Story = {
  args: {
    criteria: mockCriteria,
    expensesCategories: [
      { name: 'Groceries', transactionType: TransactionTypeEnum.EXPENSES },
      { name: 'Utilities', transactionType: TransactionTypeEnum.EXPENSES },
    ],
    revenueCategories: [
      { name: 'Salary', transactionType: TransactionTypeEnum.REVENUE },
      { name: 'Investments', transactionType: TransactionTypeEnum.REVENUE },
    ],
    datatIsLoaded: true,
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

// Create a new mockCriteria for revenue view
const revenueMockCriteria = new Criteria(
  mockBankAccount,
    GroupingEnum.month,
  new Date('2025-01-01'),
  new Date('2025-12-31'),
    TransactionTypeEnum.REVENUE
);

export const RevenueView: Story = {
  args: {
    ...Default.args,
    criteria: revenueMockCriteria
  }
};
