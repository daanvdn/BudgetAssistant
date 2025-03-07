import { Injectable } from '@angular/core';
import { MatLegacyDialog as MatDialog } from '@angular/material/legacy-dialog';
import { ErrorDialogComponent } from './error-dialog.component';

@Injectable({
  providedIn: 'root',
})
export class ErrorDialogService {
  constructor(private dialog: MatDialog) {}

  openErrorDialog(message: string, reason: string | undefined): void {
    this.dialog.open(ErrorDialogComponent, {
      data: { message: message, reason: reason },
    });
  }





}
