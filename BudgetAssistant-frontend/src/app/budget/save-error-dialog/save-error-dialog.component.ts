import {Component, Inject, OnInit} from '@angular/core';
import {MAT_DIALOG_DATA} from "@angular/material/dialog";
import {BudgetTreeNode} from "../budget.component";

@Component({
  selector: 'app-save-error-dialog',
  templateUrl: './save-error-dialog.component.html',
  styleUrls: ['./save-error-dialog.component.css']
})
export class SaveErrorDialogComponent implements OnInit {



  constructor(@Inject(MAT_DIALOG_DATA) public data: { message: string, nodes: BudgetTreeNode[] }) {

  }

  ngOnInit(): void {
  }

}
