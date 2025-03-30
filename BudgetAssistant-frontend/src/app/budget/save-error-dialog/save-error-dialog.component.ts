import {Component, Inject, OnInit} from '@angular/core';
import {
    MAT_DIALOG_DATA,
    MatDialogActions,
    MatDialogClose,
    MatDialogContent,
    MatDialogTitle
} from "@angular/material/dialog";
import {BudgetTreeNode} from "../budget.component";
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

@Component({
    selector: 'app-save-error-dialog',
    templateUrl: './save-error-dialog.component.html',
    styleUrls: ['./save-error-dialog.component.css'],
    standalone: true,
    imports: [MatDialogTitle, MatDialogContent, MatTable, MatColumnDef, MatHeaderCellDef, MatHeaderCell, MatCellDef, MatCell, MatHeaderRowDef, MatHeaderRow, MatRowDef, MatRow, MatDialogActions, MatButton, MatDialogClose]
})
export class SaveErrorDialogComponent implements OnInit {



  constructor(@Inject(MAT_DIALOG_DATA) public data: { message: string, nodes: BudgetTreeNode[] }) {

  }

  ngOnInit(): void {
  }

}
