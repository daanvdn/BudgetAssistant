import {Component, inject} from '@angular/core';
import {CommonModule} from '@angular/common';
import {MatDialogRef, MAT_DIALOG_DATA, MatDialogModule} from '@angular/material/dialog';
import {MatButtonModule} from '@angular/material/button';
import {MatIconModule} from '@angular/material/icon';
import {MatProgressSpinnerModule} from '@angular/material/progress-spinner';
import {MatSnackBar, MatSnackBarModule} from '@angular/material/snack-bar';
import {
    RuleSet, Rule, RuleUtils, Operator,
} from '../query-builder/query-builder.interfaces';
import {CategoryRead, RuleSetWrapperRead, RuleSetWrapperCreate} from './rule.models';
import {RulesService} from './rules.service';
import {PillRuleGroupComponent} from './pill-rule-group.component';

// ── Dialog data interface ─────────────────────────────────────────────
export interface RuleEditorDialogData {
    category: CategoryRead;
    ruleSetWrapper: RuleSetWrapperRead;
    ruleSet: RuleSet;
}

// ── Serialization helpers (avoids broken toJson()) ────────────────────

function resolveMatchTypeName(mt: any): string {
    if (!mt) return 'any of';
    if (typeof mt === 'object' && 'name' in mt) return mt.name;
    const s = String(mt);
    if (s === 'any') return 'any of';
    if (s === 'all') return 'all of';
    return s;
}

function serializeRuleSetForApi(ruleSet: RuleSet): { [key: string]: any } {
    return {
        clazz: 'RuleSet',
        type: 'RuleSet',
        condition: ruleSet.condition,
        rules: (ruleSet.rules || []).map((item: any) => {
            if (RuleUtils.isRuleSet(item)) {
                return serializeRuleSetForApi(item as RuleSet);
            } else if (RuleUtils.isRule(item)) {
                return serializeRuleForApi(item as Rule);
            }
            return item;
        }),
        isChild: ruleSet.isChild ?? false,
    };
}

function serializeRuleForApi(rule: Rule): { [key: string]: any } {
    const opName = rule.operator instanceof Operator
        ? rule.operator.name
        : String(rule.operator || '');
    return {
        clazz: 'Rule',
        type: 'Rule',
        field: rule.field,
        fieldType: rule.fieldType,
        value: rule.value,
        valueMatchType: resolveMatchTypeName(rule.valueMatchType),
        fieldMatchType: resolveMatchTypeName(rule.fieldMatchType),
        operator: opName,
    };
}

// ── Deep clone helpers ────────────────────────────────────────────────

function deepCloneRuleSet(rs: RuleSet): RuleSet {
    const cloned = new RuleSet(rs.condition, [], rs.collapsed, rs.isChild);
    cloned.rules = (rs.rules || []).map((item: any) => {
        if (RuleUtils.isRuleSet(item)) return deepCloneRuleSet(item as RuleSet);
        if (RuleUtils.isRule(item)) return deepCloneRule(item as Rule);
        return item;
    });
    return cloned;
}

function deepCloneRule(r: Rule): Rule {
    const cloned = new Rule();
    cloned.field = r.field ? [...r.field] : [];
    cloned.fieldType = r.fieldType;
    cloned.value = r.value ? [...r.value] : [];
    cloned.valueMatchType = r.valueMatchType;
    cloned.fieldMatchType = r.fieldMatchType;
    cloned.operator = r.operator;
    return cloned;
}

// ── Component ─────────────────────────────────────────────────────────

@Component({
    selector: 'app-rule-editor-dialog',
    templateUrl: './rule-editor-dialog.component.html',
    styleUrls: ['./rule-editor-dialog.component.scss'],
    standalone: true,
    imports: [
        CommonModule,
        MatDialogModule,
        MatButtonModule,
        MatIconModule,
        MatProgressSpinnerModule,
        MatSnackBarModule,
        PillRuleGroupComponent,
    ],
})
export class RuleEditorDialogComponent {
    private dialogRef = inject(MatDialogRef<RuleEditorDialogComponent>);
    data: RuleEditorDialogData = inject(MAT_DIALOG_DATA);
    private rulesService = inject(RulesService);
    private snackBar = inject(MatSnackBar);

    workingCopy: RuleSet;
    saving = false;
    errorMessage: string | null = null;

    constructor() {
        // Deep clone the input ruleSet so Cancel discards changes
        this.workingCopy = deepCloneRuleSet(this.data.ruleSet);
    }

    onRuleSetChange(_ruleSet: RuleSet): void {
        // Working copy is mutated in-place; this event is for potential reactivity
        this.errorMessage = null;
    }

    onSave(): void {
        this.saving = true;
        this.errorMessage = null;

        const serialized = serializeRuleSetForApi(this.workingCopy);
        const body: RuleSetWrapperCreate = {
            categoryId: this.data.ruleSetWrapper.categoryId!,
            ruleSet: serialized,
        };

        this.rulesService.saveRuleSetWrapperDirect(body).subscribe({
            next: () => {
                this.saving = false;
                this.snackBar.open('Rules saved successfully', 'OK', {duration: 3000});
                this.dialogRef.close(this.workingCopy);
            },
            error: (err) => {
                this.saving = false;
                this.errorMessage = err?.error?.detail || err?.message || 'Failed to save rules';
                this.snackBar.open(this.errorMessage!, 'Dismiss', {duration: 5000});
            },
        });
    }

    onCancel(): void {
        this.dialogRef.close();
    }
}
