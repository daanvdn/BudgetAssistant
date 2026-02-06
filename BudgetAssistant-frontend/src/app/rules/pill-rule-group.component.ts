import {Component, EventEmitter, Input, Output} from '@angular/core';
import {CommonModule} from '@angular/common';
import {MatButtonModule} from '@angular/material/button';
import {MatIconModule} from '@angular/material/icon';
import {MatTooltipModule} from '@angular/material/tooltip';
import {FieldType, Rule, RuleSet, RuleUtils, StringOperators,} from './query-builder.interfaces';
import {RULE_FIELDS_CONFIG} from './rule.models';
import {PillRuleRowComponent} from './pill-rule-row.component';

@Component({
    selector: 'app-pill-rule-group',
    templateUrl: './pill-rule-group.component.html',
    styleUrls: ['./pill-rule-group.component.scss'],
    standalone: true,
    imports: [
        CommonModule,
        MatButtonModule,
        MatIconModule,
        MatTooltipModule,
        PillRuleRowComponent,
    ],
})
export class PillRuleGroupComponent {
    @Input({required: true}) ruleSet!: RuleSet;
    @Input() depth: number = 0;
    @Input() isRoot: boolean = true;

    @Output() ruleSetChange = new EventEmitter<RuleSet>();
    @Output() remove = new EventEmitter<void>();

    readonly fieldsConfig = RULE_FIELDS_CONFIG;

    // ── Type guards ───────────────────────────────────────────────────
    isRule(item: any): boolean {
        return RuleUtils.isRule(item);
    }

    isRuleSet(item: any): boolean {
        return RuleUtils.isRuleSet(item);
    }

    asRule(item: any): Rule {
        return item as Rule;
    }

    asRuleSet(item: any): RuleSet {
        return item as RuleSet;
    }

    // ── Toggle AND / OR ───────────────────────────────────────────────
    toggleCondition(): void {
        this.ruleSet.condition = this.ruleSet.condition === 'AND' ? 'OR' : 'AND';
        this.ruleSetChange.emit(this.ruleSet);
    }

    // ── Add a new filter (default Rule) ───────────────────────────────
    addFilter(): void {
        const firstField = Object.values(this.fieldsConfig.fields)[0];
        const newRule = new Rule(
            firstField,                                   // field
            firstField.type as FieldType,                 // fieldType
            'any',                                        // fieldMatchType
            [],                                           // value
            'any',                                        // valueMatchType
            StringOperators.CONTAINS,                     // operator
        );
        this.ruleSet.rules.push(newRule);
        this.ruleSetChange.emit(this.ruleSet);
    }

    // ── Add a nested group ────────────────────────────────────────────
    addGroup(): void {
        const nestedCondition = this.ruleSet.condition === 'AND' ? 'OR' : 'AND';
        const newGroup = new RuleSet(nestedCondition, [], false, true);
        this.ruleSet.rules.push(newGroup);
        this.ruleSetChange.emit(this.ruleSet);
    }

    // ── Remove a child by index ───────────────────────────────────────
    removeChild(index: number): void {
        this.ruleSet.rules.splice(index, 1);
        this.ruleSetChange.emit(this.ruleSet);
    }

    // ── Propagate child changes ───────────────────────────────────────
    onChildChange(): void {
        this.ruleSetChange.emit(this.ruleSet);
    }
}
