import {Component, EventEmitter, Input, Output} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormsModule} from '@angular/forms';
import {MatChipsModule, MatChipInputEvent} from '@angular/material/chips';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatInputModule} from '@angular/material/input';
import {MatIconModule} from '@angular/material/icon';
import {COMMA, ENTER} from '@angular/cdk/keycodes';
import {Operator, NumericalOperators, MatchTypeOption, MATCH_TYPES} from './rule.models';

@Component({
    selector: 'app-value-editor-popover',
    templateUrl: './value-editor-popover.component.html',
    styleUrls: ['./value-editor-popover.component.scss'],
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        MatChipsModule,
        MatFormFieldModule,
        MatInputModule,
        MatIconModule,
    ],
})
export class ValueEditorPopoverComponent {
    @Input({required: true}) fieldType!: 'string' | 'categorical' | 'number';
    @Input({required: true}) values!: any[];
    @Input() matchType: MatchTypeOption | null = null;
    @Input() operator: Operator | null = null;
    @Input() fieldOptions: string[] = [];

    @Output() valuesChange = new EventEmitter<any[]>();
    @Output() matchTypeChange = new EventEmitter<MatchTypeOption>();

    readonly separatorKeyCodes = [ENTER, COMMA] as const;
    readonly matchTypes = MATCH_TYPES;

    /** For comparison operators (>, >=, <, <=), show single number input */
    get isSingleNumberInput(): boolean {
        if (this.fieldType !== 'number' || !this.operator) return false;
        const name = this.operator instanceof Operator ? this.operator.name : String(this.operator);
        return ['greater than', 'greater than or equals', 'less than', 'less than or equals'].includes(name);
    }

    addChip(event: MatChipInputEvent): void {
        const value = (event.value || '').trim();
        if (value) {
            const newValues = [...(this.values || []), value];
            this.values = newValues;
            this.valuesChange.emit(newValues);
        }
        event.chipInput?.clear();
    }

    removeChip(index: number): void {
        const newValues = [...(this.values || [])];
        newValues.splice(index, 1);
        this.values = newValues;
        this.valuesChange.emit(newValues);
    }

    onNumberChange(value: string): void {
        const num = String(value).trim();
        if (num !== '') {
            this.values = [num];
            this.valuesChange.emit([num]);
        }
    }

    onMatchTypeChange(matchType: MatchTypeOption): void {
        this.matchType = matchType;
        this.matchTypeChange.emit(matchType);
    }

    isOptionSelected(option: string): boolean {
        return (this.values || []).includes(option);
    }

    toggleOption(option: string): void {
        const newValues = [...(this.values || [])];
        const index = newValues.indexOf(option);
        if (index >= 0) {
            newValues.splice(index, 1);
        } else {
            newValues.push(option);
        }
        this.values = newValues;
        this.valuesChange.emit(newValues);
    }
}
