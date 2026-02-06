import {Component, EventEmitter, Input, Output, inject, OnChanges, SimpleChanges} from '@angular/core';
import {CommonModule} from '@angular/common';
import {MatButtonModule} from '@angular/material/button';
import {MatIconModule} from '@angular/material/icon';
import {MatTooltipModule} from '@angular/material/tooltip';

import {CategoryRead, RuleSetWrapperRead, RuleSet, SummaryNode, ruleSetToSummary} from './rule.models';
import {RulesService} from './rules.service';

@Component({
    selector: 'app-rule-summary-card',
    templateUrl: './rule-summary-card.component.html',
    styleUrls: ['./rule-summary-card.component.scss'],
    standalone: true,
    imports: [
        CommonModule,
        MatButtonModule,
        MatIconModule,
        MatTooltipModule,
    ],
})
export class RuleSummaryCardComponent implements OnChanges {
    @Input({required: true}) category!: CategoryRead;
    @Input() ruleSetWrapper: RuleSetWrapperRead | null = null;

    @Output() edit = new EventEmitter<void>();
    @Output() create = new EventEmitter<void>();

    private rulesService = inject(RulesService);

    summaryRoot: SummaryNode | null = null;
    hasRules = false;

    ngOnChanges(changes: SimpleChanges): void {
        if (changes['ruleSetWrapper']) {
            this.updateSummary();
        }
    }

    private updateSummary(): void {
        if (this.ruleSetWrapper && this.ruleSetWrapper.ruleSet) {
            try {
                const parsed: RuleSet = this.rulesService.parseRuleSet(this.ruleSetWrapper);
                if (parsed.rules && parsed.rules.length > 0) {
                    this.summaryRoot = ruleSetToSummary(parsed);
                    this.hasRules = true;
                    return;
                }
            } catch {
                // If parsing fails, treat as empty
            }
        }
        this.summaryRoot = null;
        this.hasRules = false;
    }

    onEdit(): void {
        this.edit.emit();
    }

    onCreate(): void {
        this.create.emit();
    }
}
