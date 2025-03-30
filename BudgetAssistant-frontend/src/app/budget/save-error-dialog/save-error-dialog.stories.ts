import { Meta, StoryObj, moduleMetadata } from '@storybook/angular';
import { SaveErrorDialogComponent } from './save-error-dialog.component';
import { MatDialogModule, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';

const mockData = {
  message: 'There was an error saving the budget.',
  nodes: [
    {
      budgetTreeNodeAmount: 200,
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
  ]
};

const meta: Meta<SaveErrorDialogComponent> = {
  title: 'Components/SaveErrorDialog',
  component: SaveErrorDialogComponent,
  decorators: [
    moduleMetadata({
      imports: [MatDialogModule, BrowserAnimationsModule],
      providers: [
        { provide: MAT_DIALOG_DATA, useValue: mockData }
      ]
    })
  ]
};

export default meta;
type Story = StoryObj<SaveErrorDialogComponent>;

export const Default: Story = {
  args: {}
};

// Adding more story variations
export const MultipleErrorNodes: Story = {
  args: {},
  decorators: [
    moduleMetadata({
      providers: [
        { provide: MAT_DIALOG_DATA, useValue: {
            message: 'Multiple budget categories have validation issues.',
            nodes: [
              {
                budgetTreeNodeAmount: 200,
                budgetTreeNodeId: 10,
                budgetTreeNodeParentId: 0,
                name: 'Housing',
                qualifiedName: 'Housing'
              },
              {
                budgetTreeNodeAmount: 150,
                budgetTreeNodeId: 11,
                budgetTreeNodeParentId: 0,
                name: 'Transportation',
                qualifiedName: 'Transportation'
              },
              {
                budgetTreeNodeAmount: 300,
                budgetTreeNodeId: 12,
                budgetTreeNodeParentId: 0,
                name: 'Entertainment',
                qualifiedName: 'Entertainment'
              }
            ]
          }}
      ]
    })
  ]
};

export const NoErrorNodes: Story = {
  args: {},
  decorators: [
    moduleMetadata({
      providers: [
        { provide: MAT_DIALOG_DATA, useValue: {
            message: 'An error occurred, but no specific budget categories were identified.',
            nodes: []
          }}
      ]
    })
  ]
};

export const LongCategoryNames: Story = {
  args: {},
  decorators: [
    moduleMetadata({
      providers: [
        { provide: MAT_DIALOG_DATA, useValue: {
            message: 'Categories with very long names have validation issues.',
            nodes: [
              {
                budgetTreeNodeAmount: 500,
                budgetTreeNodeId: 20,
                budgetTreeNodeParentId: 0,
                name: 'Extraordinary Miscellaneous Expenses That Are Very Difficult To Categorize Properly And Need Review',
                qualifiedName: 'Extraordinary Miscellaneous Expenses That Are Very Difficult To Categorize Properly And Need Review'
              }
            ]
          }}
      ]
    })
  ]
};

export const DutchLanguage: Story = {
  args: {},
  decorators: [
    moduleMetadata({
      providers: [
        { provide: MAT_DIALOG_DATA, useValue: {
            message: 'De totale uitgaven in deze categorieën overschrijden het beschikbare budget.',
            nodes: [
              {
                budgetTreeNodeAmount: 450,
                budgetTreeNodeId: 30,
                budgetTreeNodeParentId: 0,
                name: 'Boodschappen',
                qualifiedName: 'Boodschappen'
              },
              {
                budgetTreeNodeAmount: 300,
                budgetTreeNodeId: 31,
                budgetTreeNodeParentId: 0,
                name: 'Huishoudelijke kosten',
                qualifiedName: 'Huishoudelijke kosten'
              }
            ]
          }}
      ]
    })
  ]
};