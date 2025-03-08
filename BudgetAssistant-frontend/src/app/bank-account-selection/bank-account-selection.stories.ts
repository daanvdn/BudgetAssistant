import type {Meta, StoryObj} from '@storybook/angular';
import {moduleMetadata} from '@storybook/angular';
import {BankAccountSelectionComponent} from './bank-account-selection.component';
import {ReactiveFormsModule} from '@angular/forms';
import {BehaviorSubject} from 'rxjs';
import {AppService} from '../app.service';
import {BankAccount} from '@daanvdn/budget-assistant-client';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatSelectModule} from '@angular/material/select';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {IbanPipe} from '../iban.pipe';

// Mock BankAccount data
const mockBankAccounts: BankAccount[] = [
    {accountNumber: 'NL91ABNA0417164300', alias: 'Main Account', users: [1]},
    {accountNumber: 'NL39RABO0300065264', alias: 'Savings', users: [1]},
    {accountNumber: 'NL20INGB0001234567', alias: null, users: [1, 2]},
];

// Mock AppService
const mockAppService = {
    fetchBankAccountsForUser: () => new BehaviorSubject(mockBankAccounts),
    setBankAccount: () => {
    }
};

const meta: Meta<BankAccountSelectionComponent> = {
    title: 'Components/BankAccountSelection',
    component: BankAccountSelectionComponent,
    decorators: [
        moduleMetadata({
            imports: [
                ReactiveFormsModule,
                MatFormFieldModule,
                MatSelectModule,
                NoopAnimationsModule,
                IbanPipe
            ],
            declarations: [],
            providers: [
                {provide: AppService, useValue: mockAppService}
            ],
        }),
    ],
    parameters: {
        layout: 'centered',
    },
    argTypes: {
        change: {action: 'changed'}
    },
};

export default meta;
type Story = StoryObj<BankAccountSelectionComponent>;

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
                    useValue: {
                        fetchBankAccountsForUser: () => new BehaviorSubject([]),
                        setBankAccount: () => {
                        }
                    }
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
                            {accountNumber: 'NL91ABNA0417164300', alias: 'Main Account', users: [1]}
                        ]),
                        setBankAccount: () => {
                        }
                    }
                }
            ],
        }),
    ],
};

export const MultipleAccounts: Story = {
    args: {},
    decorators: [
        moduleMetadata({
            providers: [
                {
                    provide: AppService,
                    useValue: {
                        fetchBankAccountsForUser: () => new BehaviorSubject(mockBankAccounts),
                        setBankAccount: () => {
                        }
                    }
                }
            ],
        }),
    ],
}