import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogTitle, MatDialogContent, MatDialogActions, MatDialogClose } from '@angular/material/dialog';
import { CdkScrollable } from '@angular/cdk/scrolling';
import { NgIf } from '@angular/common';
import { MatLabel } from '@angular/material/form-field';
import { MatButton } from '@angular/material/button';

@Component({
    selector: 'app-error-dialog',
    templateUrl: './error-dialog.component.html',
    standalone: true,
    imports: [
        MatDialogTitle,
        CdkScrollable,
        MatDialogContent,
        NgIf,
        MatLabel,
        MatDialogActions,
        MatButton,
        MatDialogClose,
    ],
})
export class ErrorDialogComponent {
  constructor(@Inject(MAT_DIALOG_DATA) public data: { message: string, reason: string }) {}
}
