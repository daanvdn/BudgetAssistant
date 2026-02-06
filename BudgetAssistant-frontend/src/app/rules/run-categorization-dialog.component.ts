import {Component, inject, OnInit} from '@angular/core';
import {CommonModule} from '@angular/common';
import {MatDialogRef, MatDialogTitle, MatDialogContent, MatDialogActions, MatDialogClose} from '@angular/material/dialog';
import {MatButtonModule} from '@angular/material/button';
import {MatProgressSpinnerModule} from '@angular/material/progress-spinner';
import {MatIconModule} from '@angular/material/icon';

import {CategorizeTransactionsResponse} from './rule.models';
import {RulesService} from './rules.service';

@Component({
    selector: 'app-run-categorization-dialog',
    templateUrl: './run-categorization-dialog.component.html',
    styleUrls: ['./run-categorization-dialog.component.scss'],
    standalone: true,
    imports: [
        CommonModule,
        MatDialogTitle,
        MatDialogContent,
        MatDialogActions,
        MatDialogClose,
        MatButtonModule,
        MatProgressSpinnerModule,
        MatIconModule,
    ],
})
export class RunCategorizationDialogComponent implements OnInit {
    private dialogRef = inject(MatDialogRef<RunCategorizationDialogComponent>);
    private rulesService = inject(RulesService);

    loading = true;
    error: string | null = null;
    result: CategorizeTransactionsResponse | null = null;

    ngOnInit(): void {
        this.rulesService.categorizeTransactions().subscribe({
            next: (response) => {
                this.result = response;
                this.loading = false;
            },
            error: (err) => {
                this.error = err?.message ?? 'An unknown error occurred';
                this.loading = false;
            },
        });
    }

    close(): void {
        this.dialogRef.close();
    }
}
