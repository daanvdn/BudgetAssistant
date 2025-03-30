// src/app/category-details/category-details.stories.ts
import { Meta, StoryObj, moduleMetadata } from '@storybook/angular';
import { CategoryDetailsComponent } from './category-details.component';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import {
    ExpensesRecurrenceEnum,
    TransactionTypeEnum,
    GroupingEnum,
    RevenueRecurrenceEnum
} from '@daanvdn/budget-assistant-client';
import { Criteria } from '../insights/insights.component';
import { AppService } from '../app.service';
import { of, throwError } from 'rxjs';
import { MatSelectionList } from '@angular/material/list';
import { ChartModule } from 'primeng/chart';
import { action } from '@storybook/addon-actions';
import { userEvent, within, waitFor } from '@storybook/test';

// Helper to generate mock chart data
const generateMockData = (categoryName: string, periods: string[] = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'], baseValue: number = 100) => {
    return {
        labels: periods,
        datasets: [
            {
                label: categoryName,
                data: periods.map(() => Math.floor(Math.random() * baseValue + baseValue/2)),
                maxBarThickness: 50
            }
        ]
    };
};

// Mock AppService
const mockAppService = {
    selectedBankAccountObservable$: of({
        accountNumber: 'BE123456789',
        alias: 'Main Account',
        users: [1]
    }),
    getCategoriesForAccountAndTransactionType: (accountNumber: string, transactionType: TransactionTypeEnum) => {
        if (transactionType === TransactionTypeEnum.EXPENSES) {
            return of(['Groceries', 'Rent', 'Transportation', 'Entertainment', 'Utilities', 'Healthcare']);
        } else {
            return of(['Salary', 'Investments', 'Freelance', 'Gifts', 'Refunds']);
        }
    },
    getCategoryDetailsForPeriod: (query: any, categoryName: string) => {
        action('getCategoryDetailsForPeriod')(query, categoryName);
        return of(generateMockData(categoryName));
    }
};

const meta: Meta<CategoryDetailsComponent> = {
    title: 'Components/CategoryDetails',
    component: CategoryDetailsComponent,
    decorators: [
        moduleMetadata({
            imports: [BrowserAnimationsModule, MatSelectionList, ChartModule],
            providers: [
                { provide: AppService, useValue: mockAppService }
            ]
        })
    ],
    parameters: {
        layout: 'fullscreen',
    },
    argTypes: {
        criteria: {
            control: 'object',
            description: 'Filtering criteria for the component'
        }
    }
};

export default meta;
type Story = StoryObj<CategoryDetailsComponent>;

// Base criteria for reuse
const baseCriteria = new Criteria(
    {
        accountNumber: 'BE123456789',
        alias: 'Main Account',
        users: [1]
    },
    GroupingEnum.month,
    new Date(2023, 0, 1),
    new Date(2023, 5, 31),
    TransactionTypeEnum.EXPENSES
);

// Basic expenses view
export const ExpensesView: Story = {
    args: {
        criteria: baseCriteria
    },
    play: async ({ canvasElement }) => {
        const canvas = within(canvasElement);

        // Wait for categories to load
        await waitFor(() => expect(canvas.getByText('Groceries')).toBeInTheDocument());

        // Select a category
        await userEvent.click(canvas.getByText('Rent'));

        // Wait for chart to render
        await waitFor(() => expect(canvas.getByRole('img')).toBeInTheDocument(), { timeout: 2000 });
    }
};
/*

// Revenue view
export const RevenueView: Story = {
    args: {
        criteria: {
            ...baseCriteria,
            transactionType: TransactionTypeEnum.REVENUE
        }
    },
    play: async ({ canvasElement }) => {
        const canvas = within(canvasElement);
        await waitFor(() => expect(canvas.getByText('Salary')).toBeInTheDocument());
        await userEvent.click(canvas.getByText('Investments'));
    }
};

// Quarterly grouping
export const QuarterlyView: Story = {
    args: {
        criteria: {
            ...baseCriteria,
            grouping: GroupingEnum.quarter
        }
    },
    parameters: {
        mockData: {
            getCategoryDetailsForPeriod: () => of({
                labels: ['Q1 2023', 'Q2 2023'],
                datasets: [{
                    label: 'Utilities',
                    data: [350, 410],
                    maxBarThickness: 50
                }]
            })
        }
    },
    play: async ({ canvasElement }) => {
        const canvas = within(canvasElement);
        await waitFor(() => expect(canvas.getByText('Utilities')).toBeInTheDocument());
        await userEvent.click(canvas.getByText('Utilities'));
    }
};

// Yearly grouping
export const YearlyView: Story = {
    args: {
        criteria: {
            ...baseCriteria,
            grouping: GroupingEnum.year,
            startDate: new Date(2020, 0, 1),
            endDate: new Date(2023, 11, 31)
        }
    },
    parameters: {
        mockData: {
            getCategoryDetailsForPeriod: () => of({
                labels: ['2020', '2021', '2022', '2023'],
                datasets: [{
                    label: 'Healthcare',
                    data: [1200, 1350, 1480, 1600],
                    maxBarThickness: 50
                }]
            })
        }
    },
    play: async ({ canvasElement }) => {
        const canvas = within(canvasElement);
        await waitFor(() => expect(canvas.getByText('Healthcare')).toBeInTheDocument());
        await userEvent.click(canvas.getByText('Healthcare'));
    }
};

// Recurring expenses
export const RecurringExpenses: Story = {
    args: {
        criteria: { ...baseCriteria }
    },
    parameters: {
        mockData: {
            getCategoryDetailsForPeriod: (query: any) => of({
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'Rent (Recurring)',
                    data: [800, 800, 800, 800, 800, 800],
                    maxBarThickness: 50
                }]
            })
        }
    },
    play: async ({ canvasElement }) => {
        const canvas = within(canvasElement);
        await waitFor(() => expect(canvas.getByText('Rent')).toBeInTheDocument());
        await userEvent.click(canvas.getByText('Rent'));
    }
};

// Non-recurring expenses
export const NonRecurringExpenses: Story = {
    args: {
        criteria: { ...baseCriteria }
    },
    parameters: {
        mockData: {
            getCategoryDetailsForPeriod: (query: any) => of({
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'Entertainment (Non-recurring)',
                    data: [120, 0, 85, 200, 0, 150],
                    maxBarThickness: 50
                }]
            })
        }
    },
    play: async ({ canvasElement }) => {
        const canvas = within(canvasElement);
        await waitFor(() => expect(canvas.getByText('Entertainment')).toBeInTheDocument());
        await userEvent.click(canvas.getByText('Entertainment'));
    }
};

// Empty state when no criteria provided
export const NoCriteriaState: Story = {
    args: {
        criteria: undefined
    }
};

// Error state
export const ErrorState: Story = {
    args: {
        criteria: { ...baseCriteria }
    },
    parameters: {
        mockData: {
            getCategoriesForAccountAndTransactionType: () => throwError(() => new Error('Failed to load categories'))
        }
    }
};

// Transaction type change
export const TransactionTypeChange: Story = {
    args: {
        criteria: { ...baseCriteria }
    },
    play: async ({ canvasElement, args }) => {
        const canvas = within(canvasElement);

        // First show expenses
        await waitFor(() => expect(canvas.getByText('Groceries')).toBeInTheDocument());
        await userEvent.click(canvas.getByText('Groceries'));

        // Then change to revenue
        args.criteria = {
            ...args.criteria,
            transactionType: TransactionTypeEnum.REVENUE
        };

        // Wait for revenue categories to appear
        await waitFor(() => expect(canvas.getByText('Salary')).toBeInTheDocument());
        await userEvent.click(canvas.getByText('Salary'));
    }
};*/
