import type { Meta, StoryObj } from '@storybook/angular';
import { BankAccountCheckBoxesComponent } from './bank-account-check-boxes.component';
import { moduleMetadata } from '@storybook/angular';
import { ReactiveFormsModule } from '@angular/forms';
import { BehaviorSubject } from 'rxjs';
import { AppService } from '../app.service';
import { BankAccount } from '@daanvdn/budget-assistant-client';
import { MatCheckboxModule } from '@angular/material/checkbox';

// Mock BankAccount data
const mockBankAccounts: BankAccount[] = [
  { accountNumber: 'NL91ABNA0417164300', alias: 'Main Account', users: [1] },
  { accountNumber: 'NL39RABO0300065264', alias: 'Savings', users: [1] },
  { accountNumber: 'NL20INGB0001234567', alias: null, users: [1, 2] },
];

// Mock AppService
const mockAppService = {
  fetchBankAccountsForUser: () => new BehaviorSubject(mockBankAccounts)
};

const meta: Meta<BankAccountCheckBoxesComponent> = {
  title: 'Components/BankAccountCheckBoxes',
  component: BankAccountCheckBoxesComponent,
  decorators: [
    moduleMetadata({
      imports: [ReactiveFormsModule, MatCheckboxModule],
      providers: [
        { provide: AppService, useValue: mockAppService }
      ],
    }),
  ],
  parameters: {
    layout: 'centered',
  },
  argTypes: {
    change: { action: 'changed' }
  },
};

export default meta;
type Story = StoryObj<BankAccountCheckBoxesComponent>;

export const Default: Story = {
  args: {},
};

export const NoAccountsAvailable: Story = {
  args: {},
  decorators: [
    moduleMetadata({
      providers: [
        {
          provide: AppService,
          useValue: { fetchBankAccountsForUser: () => new BehaviorSubject([]) }
        }
      ],
    }),
  ],
};

export const SingleAccount: Story = {
  args: {},
  decorators: [
    moduleMetadata({
      providers: [
        {
          provide: AppService,
          useValue: {
            fetchBankAccountsForUser: () => new BehaviorSubject([
              { accountNumber: 'NL91ABNA0417164300', alias: 'Main Account', users: [1] }
            ])
          }
        }
      ],
    }),
  ],
};