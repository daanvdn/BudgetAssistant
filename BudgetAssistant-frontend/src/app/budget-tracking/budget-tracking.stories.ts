import type { Meta, StoryObj } from '@storybook/angular';
import { moduleMetadata } from '@storybook/angular';
import { BudgetTrackingComponent } from './budget-tracking.component';
import { BehaviorSubject, of } from 'rxjs';
import { AppService } from '../app.service';
import { BankAccountRead, Grouping, TransactionTypeEnum, BudgetAssistantApiService, BudgetTrackerResult as ApiBudgetTrackerResult, RecurrenceType } from '@daanvdn/budget-assistant-client';
import { MatTableModule } from '@angular/material/table';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { NgFor, NgIf } from '@angular/common';
import { Criteria } from '../model/criteria.model';
import { BudgetTrackerResult } from '../model';

// Mock BankAccount data
const mockBankAccount: BankAccountRead = {
  accountNumber: 'NL91ABNA0417164300',
  alias: 'Main Account'
};

// Mock Criteria
const mockCriteria = new Criteria(
  mockBankAccount,
  Grouping.MONTH,
  new Date('2023-01-01'),
  new Date('2023-12-31'),
  TransactionTypeEnum.BOTH
);

// Mock BudgetTrackerResult data (for the local model)
const mockBudgetTrackerResult: BudgetTrackerResult = {
  columns: ['Category', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Total'],
  data: [
    {
      data: {
        'Category': 'Household Expenses',
        'Jan': 1200,
        'Feb': 1150,
        'Mar': 1300,
        'Apr': 1250,
        'May': 1100,
        'Jun': 1180,
        'Total': 7180
      },
      children: [
        {
          data: {
            'Category': 'Groceries',
            'Jan': 500,
            'Feb': 450,
            'Mar': 550,
            'Apr': 480,
            'May': 520,
            'Jun': 490,
            'Total': 2990
          },
          children: [],
          leaf: true
        },
        {
          data: {
            'Category': 'Utilities',
            'Jan': 350,
            'Feb': 380,
            'Mar': 360,
            'Apr': 370,
            'May': 340,
            'Jun': 390,
            'Total': 2190
          },
          children: [],
          leaf: true
        },
        {
          data: {
            'Category': 'Rent',
            'Jan': 350,
            'Feb': 320,
            'Mar': 390,
            'Apr': 400,
            'May': 240,
            'Jun': 300,
            'Total': 2000
          },
          children: [],
          leaf: true
        }
      ],
      leaf: false
    },
    {
      data: {
        'Category': 'Transportation',
        'Jan': 300,
        'Feb': 280,
        'Mar': 320,
        'Apr': 290,
        'May': 310,
        'Jun': 330,
        'Total': 1830
      },
      children: [
        {
          data: {
            'Category': 'Fuel',
            'Jan': 150,
            'Feb': 140,
            'Mar': 160,
            'Apr': 145,
            'May': 155,
            'Jun': 165,
            'Total': 915
          },
          children: [],
          leaf: true
        },
        {
          data: {
            'Category': 'Public Transport',
            'Jan': 150,
            'Feb': 140,
            'Mar': 160,
            'Apr': 145,
            'May': 155,
            'Jun': 165,
            'Total': 915
          },
          children: [],
          leaf: true
        }
      ],
      leaf: false
    }
  ]
};

// Mock API BudgetTrackerResult (matches new API structure)
const mockApiBudgetTrackerResult: ApiBudgetTrackerResult = {
  period: '2023',
  startDate: '2023-01-01',
  endDate: '2023-12-31',
  entries: [
    { categoryQualifiedName: 'EXPENSES.Household', categoryName: 'Household Expenses', budgetedAmount: 7000, actualAmount: 7180, difference: -180 },
    { categoryQualifiedName: 'EXPENSES.Transportation', categoryName: 'Transportation', budgetedAmount: 2000, actualAmount: 1830, difference: 170 }
  ],
  totalBudgeted: 9000,
  totalActual: 9010,
  totalDifference: -10
};

// Mock empty BudgetTrackerResult
const emptyApiBudgetTrackerResult: ApiBudgetTrackerResult = {
  period: '2023',
  startDate: '2023-01-01',
  endDate: '2023-12-31',
  entries: [],
  totalBudgeted: 0,
  totalActual: 0,
  totalDifference: 0
};

// Mock BudgetAssistantApiService
const mockBudgetAssistantApiService = {
  analysis: {
    trackBudgetApiAnalysisTrackBudgetPost: () => of(mockApiBudgetTrackerResult)
  }
};

// Mock empty BudgetAssistantApiService
const emptyBudgetAssistantApiService = {
  analysis: {
    trackBudgetApiAnalysisTrackBudgetPost: () => of(emptyApiBudgetTrackerResult)
  }
};

const meta: Meta<BudgetTrackingComponent> = {
  title: 'Components/BudgetTracking',
  component: BudgetTrackingComponent,
  decorators: [
    moduleMetadata({
      imports: [
        MatTableModule,
        NoopAnimationsModule,
        NgIf,
        NgFor
      ],
      providers: [
        { provide: AppService, useValue: {} },
        { provide: BudgetAssistantApiService, useValue: mockBudgetAssistantApiService }
      ],
    }),
  ],
  parameters: {
    layout: 'fullscreen',
  },
};

export default meta;
type Story = StoryObj<BudgetTrackingComponent>;

export const Default: Story = {
  args: {
    criteria: mockCriteria
  }
};

export const EmptyData: Story = {
  args: {
    criteria: mockCriteria
  },
  decorators: [
    moduleMetadata({
      providers: [
        { provide: AppService, useValue: {} },
        { provide: BudgetAssistantApiService, useValue: emptyBudgetAssistantApiService }
      ],
    }),
  ],
};

export const Loading: Story = {
  args: {
    criteria: undefined
  }
};
