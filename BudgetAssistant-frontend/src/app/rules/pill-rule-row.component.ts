import {Component, EventEmitter, Input, Output} from '@angular/core';
import {CommonModule} from '@angular/common';
import {MatMenuModule} from '@angular/material/menu';
import {MatButtonModule} from '@angular/material/button';
import {MatIconModule} from '@angular/material/icon';
import {MatTooltipModule} from '@angular/material/tooltip';
import {
    Rule, Operator, Field, FieldTypeEnum, MatchTypeOption, MatchTypes,
    StringOperators, CategoricalOperators, NumericalOperators,
    QueryBuilderConfig,
} from '../query-builder/query-builder.interfaces';
import {ValueEditorPopoverComponent} from './value-editor-popover.component';

@Component({
    selector: 'app-pill-rule-row',
    templateUrl: './pill-rule-row.component.html',
    styleUrls: ['./pill-rule-row.component.scss'],
    standalone: true,
    imports: [
        CommonModule,
        MatMenuModule,
        MatButtonModule,
        MatIconModule,
        MatTooltipModule,
        ValueEditorPopoverComponent,
    ],
})
export class PillRuleRowComponent {
    @Input({required: true}) rule!: Rule;
    @Input({required: true}) fieldsConfig!: QueryBuilderConfig;

    @Output() ruleChange = new EventEmitter<Rule>();
    @Output() remove = new EventEmitter<void>();

    // ── Field groups for dropdown menu ────────────────────────────────
    get fieldGroups(): { label: string; fields: Field[] }[] {
        const fields = Object.values(this.fieldsConfig.fields);
        const groups = new Map<string, Field[]>();
        for (const field of fields) {
            const type = field.type === 'category' ? 'categorical' : field.type;
            if (!groups.has(type)) groups.set(type, []);
            groups.get(type)!.push(field);
        }
        const labelMap: Record<string, string> = {
            string: 'String fields',
            categorical: 'Categorical fields',
            number: 'Number fields',
        };
        return Array.from(groups.entries()).map(([type, flds]) => ({
            label: labelMap[type] || type,
            fields: flds,
        }));
    }

    // ── Resolved field from config ────────────────────────────────────
    get resolvedField(): Field | undefined {
        if (!this.rule.field || this.rule.field.length === 0) return undefined;
        const path = this.rule.field.join('.');
        return Object.values(this.fieldsConfig.fields).find(f => f.pathFromTransaction === path);
    }

    get fieldDisplayName(): string {
        const field = this.resolvedField;
        return field?.value || field?.name || this.rule.field?.join('.') || '(select field)';
    }

    // ── Resolved operator ─────────────────────────────────────────────
    get resolvedOperator(): Operator | undefined {
        if (!this.rule.operator) return undefined;
        if (this.rule.operator instanceof Operator) return this.rule.operator;
        const name = String(this.rule.operator);
        const allOps = [...StringOperators.ALL, ...CategoricalOperators.ALL, ...NumericalOperators.ALL];
        return allOps.find(op => op.name === name || op.value === name);
    }

    get availableOperators(): Operator[] {
        const type = this.rule.fieldType || this.resolvedField?.type;
        switch (type) {
            case 'string':
                return StringOperators.ALL;
            case 'categorical':
            case 'category':
                return CategoricalOperators.ALL;
            case 'number':
                return NumericalOperators.ALL;
            default:
                return StringOperators.ALL;
        }
    }

    get operatorDisplayLabel(): string {
        const op = this.resolvedOperator;
        if (!op) return '(operator)';
        if (this.rule.fieldType === 'number' || this.resolvedField?.type === 'number') {
            return this.getNumberPillLabel(op);
        }
        if (op.name === 'fuzzy match') return 'fuzzy matches';
        return op.name;
    }

    getNumberPillLabel(op: Operator): string {
        switch (op.name) {
            case 'equals':
                return '=';
            case 'not equals':
                return '≠';
            case 'greater than':
                return '>';
            case 'greater than or equals':
                return '≥';
            case 'less than':
                return '<';
            case 'less than or equals':
                return '≤';
            default:
                return op.name;
        }
    }

    getOperatorMenuLabel(op: Operator): string {
        if (this.rule.fieldType === 'number' || this.resolvedField?.type === 'number') {
            const symbol = this.getNumberPillLabel(op);
            return `${op.name} (${symbol})`;
        }
        return op.name;
    }

    // ── Value display ─────────────────────────────────────────────────
    get valueDisplayText(): string {
        const values = this.rule.value || [];
        if (values.length === 0) return '(click to add values)';
        if (values.length <= 3) return values.join(', ');
        return `${values.slice(0, 2).join(', ')}, +${values.length - 2}`;
    }

    // ── Resolved types for value editor ───────────────────────────────
    get resolvedFieldType(): 'string' | 'categorical' | 'number' {
        const type = this.rule.fieldType || this.resolvedField?.type || 'string';
        if (type === 'category') return 'categorical';
        return type as 'string' | 'categorical' | 'number';
    }

    get resolvedMatchType(): MatchTypeOption {
        const mt = this.rule.valueMatchType;
        if (!mt) return MatchTypes.ANY_OF;
        if (typeof mt === 'object' && 'name' in mt) return mt as unknown as MatchTypeOption;
        const mtStr = String(mt);
        if (mtStr === 'any' || mtStr === 'any of') return MatchTypes.ANY_OF;
        if (mtStr === 'all' || mtStr === 'all of') return MatchTypes.ALL_OF;
        return MatchTypes.ANY_OF;
    }

    get fieldOptions(): string[] {
        const field = this.resolvedField;
        if (!field || !field.options) return [];
        return field.options.map(o => String(o.value ?? o.name));
    }

    // ── Actions ───────────────────────────────────────────────────────
    selectField(field: Field): void {
        this.rule.field = [field.pathFromTransaction];
        this.rule.fieldType = (field.type === 'category' ? 'categorical' : field.type) as FieldTypeEnum;

        // Reset operator to first available for the new type
        const ops = field.operators || [];
        this.rule.operator = ops.length > 0 ? ops[0] : undefined;

        // Clear values
        this.rule.value = [];

        // Ensure match types are set
        if (!this.rule.fieldMatchType) this.rule.fieldMatchType = 'any';
        if (!this.rule.valueMatchType) this.rule.valueMatchType = 'any';

        this.ruleChange.emit(this.rule);
    }

    selectOperator(op: Operator): void {
        this.rule.operator = op;
        this.ruleChange.emit(this.rule);
    }

    onValuesChange(values: any[]): void {
        this.rule.value = values.map(v => String(v));
        this.ruleChange.emit(this.rule);
    }

    onMatchTypeChange(matchType: MatchTypeOption): void {
        this.rule.valueMatchType = matchType.value;
        this.ruleChange.emit(this.rule);
    }
}
