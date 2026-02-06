import {Component, inject} from '@angular/core';
import {
  MAT_DIALOG_DATA,
  MatDialogActions,
  MatDialogClose,
  MatDialogContent,
  MatDialogTitle
} from '@angular/material/dialog';
import {
  MatCell,
  MatCellDef,
  MatColumnDef,
  MatHeaderCell,
  MatHeaderCellDef,
  MatHeaderRow,
  MatHeaderRowDef,
  MatRow,
  MatRowDef,
  MatTable
} from '@angular/material/table';
import {MatButton} from '@angular/material/button';
import {BudgetTreeNodeRead} from '@daanvdn/budget-assistant-client';
import {CurrencyPipe} from '@angular/common';

export interface SaveErrorDialogData {
  message: string;
  nodes: BudgetTreeNodeRead[];
}

@Component({
  selector: 'app-save-error-dialog',
  templateUrl: './save-error-dialog.component.html',
  styleUrls: ['./save-error-dialog.component.scss'],
  standalone: true,
  imports: [
    MatDialogTitle,
    MatDialogContent,
    MatTable,
    MatColumnDef,
    MatHeaderCellDef,
    MatHeaderCell,
    MatCellDef,
    MatCell,
    MatHeaderRowDef,
    MatHeaderRow,
    MatRowDef,
    MatRow,
    MatDialogActions,
    MatButton,
    MatDialogClose,
    CurrencyPipe
  ]
})
export class SaveErrorDialogComponent {
  readonly data = inject<SaveErrorDialogData>(MAT_DIALOG_DATA);
  readonly displayedColumns = ['categorie', 'maandbudget'];
}
