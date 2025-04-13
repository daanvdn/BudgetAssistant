import type { Meta, StoryObj } from '@storybook/angular';
import { moduleMetadata } from '@storybook/angular';
import { BudgetTrackingComponent } from './budget-tracking.component';
import { BehaviorSubject, of } from 'rxjs';
import { AppService } from '../app.service';
import { BankAccount, GroupingEnum, TransactionTypeEnum } from '@daanvdn/budget-assistant-client';
import { MatTableModule } from '@angular/material/table';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { NgFor, NgIf } from '@angular/common';
import { Criteria } from '../model/criteria.model';
import { ApiBudgetAssistantBackendClientService } from '@daanvdn/budget-assistant-client';
import { BudgetTrackerResult } from '../model';

// Mock BankAccount data
const mockBankAccount: BankAccount = {
  accountNumber: 'NL91ABNA0417164300',
  alias: 'Main Account',
  users: [1]
};

// Mock Criteria
const mockCriteria = new Criteria(
  mockBankAccount,
  GroupingEnum.month,
  new Date('2023-01-01'),
  new Date('2023-12-31'),
  TransactionTypeEnum.BOTH
);

// Mock BudgetTrackerResult data
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

// Mock empty BudgetTrackerResult
const emptyBudgetTrackerResult: BudgetTrackerResult = {
  columns: ['Category', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Total'],
  data: []
};

// Mock ApiBudgetAssistantBackendClientService
const mockApiBudgetAssistantBackendClientService = {
  apiTrackBudgetCreate: () => of(mockBudgetTrackerResult)
};

// Mock empty ApiBudgetAssistantBackendClientService
const emptyApiBudgetAssistantBackendClientService = {
  apiTrackBudgetCreate: () => of(emptyBudgetTrackerResult)
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
        { provide: ApiBudgetAssistantBackendClientService, useValue: mockApiBudgetAssistantBackendClientService }
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
        { provide: ApiBudgetAssistantBackendClientService, useValue: emptyApiBudgetAssistantBackendClientService }
      ],
    }),
  ],
};

export const Loading: Story = {
  args: {
    criteria: undefined
  }
};
