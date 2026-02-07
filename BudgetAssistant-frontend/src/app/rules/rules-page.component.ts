import {Component, inject, OnInit, signal, WritableSignal, OnDestroy} from '@angular/core';
import {CommonModule} from '@angular/common';
import {MatToolbar} from '@angular/material/toolbar';
import {MatButtonToggleChange, MatButtonToggleGroup, MatButtonToggle} from '@angular/material/button-toggle';
import {MatButtonModule} from '@angular/material/button';
import {MatIconModule} from '@angular/material/icon';
import {MatTooltipModule} from '@angular/material/tooltip';
import {MatDialog} from '@angular/material/dialog';
import {MatProgressSpinnerModule} from '@angular/material/progress-spinner';
import {MatExpansionModule} from '@angular/material/expansion';
import {MatChipsModule} from '@angular/material/chips';
import {firstValueFrom, Subscription} from 'rxjs';
import {injectQueryClient} from '@tanstack/angular-query-experimental';

import {CategoryRead, RuleSetWrapperRead, RuleSet, TransactionTypeEnum} from './rule.models';
import {RulesService} from './rules.service';
import {AppService} from '../app.service';
import {RuleSummaryCardComponent} from './rule-summary-card.component';
import {RunCategorizationDialogComponent} from './run-categorization-dialog.component';
import {RuleEditorDialogComponent, RuleEditorDialogData} from './rule-editor-dialog.component';

type ActiveView = 'expenses' | 'revenue';

@Component({
    selector: 'app-rules-page',
    templateUrl: './rules-page.component.html',
    styleUrls: ['./rules-page.component.scss'],
    standalone: true,
    imports: [
        CommonModule,
        MatToolbar,
        MatButtonToggleGroup,
        MatButtonToggle,
        MatButtonModule,
        MatIconModule,
        MatTooltipModule,
        MatProgressSpinnerModule,
        MatExpansionModule,
        MatChipsModule,
        RuleSummaryCardComponent,
    ],
})
export class RulesPageComponent implements OnInit, OnDestroy {
    private appService = inject(AppService);
    private rulesService = inject(RulesService);
    private dialog = inject(MatDialog);
    private queryClient = injectQueryClient();

    activeView: WritableSignal<ActiveView> = signal('expenses');

    // Flat category lists for both views
    expensesFlatCategories: CategoryRead[] = [];
    revenueFlatCategories: CategoryRead[] = [];

    // Cache of loaded rule set wrappers keyed by category qualifiedName
    ruleSetWrapperCache = new Map<string, RuleSetWrapperRead>();
    loadingCategories = new Set<string>();
    errorCategories = new Set<string>();

    private subscriptions: Subscription[] = [];

    private static readonly ILLEGAL_NODES = ['NO CATEGORY', 'DUMMY CATEGORY'];

    ngOnInit(): void {
        const expSub = this.appService.sharedCategoryTreeExpenses.subscribe(nodes => {
            this.expensesFlatCategories = this.flattenAndSort(this.filterNodes(nodes));
            this.preloadRuleSets(this.expensesFlatCategories, TransactionTypeEnum.EXPENSES);
        });

        const revSub = this.appService.sharedCategoryTreeRevenue.subscribe(nodes => {
            this.revenueFlatCategories = this.flattenAndSort(this.filterNodes(nodes));
            this.preloadRuleSets(this.revenueFlatCategories, TransactionTypeEnum.REVENUE);
        });

        this.subscriptions.push(expSub, revSub);
    }

    /** Eagerly load rule set wrappers for all categories so the empty chip can show immediately */
    private preloadRuleSets(categories: CategoryRead[], type: TransactionTypeEnum): void {
        for (const category of categories) {
            const key = category.qualifiedName;
            if (this.ruleSetWrapperCache.has(key) || this.loadingCategories.has(key)) {
                continue;
            }
            this.loadingCategories.add(key);
            this.queryClient.fetchQuery({
                queryKey: ['ruleSetWrapper', key, type],
                queryFn: () => firstValueFrom(this.rulesService.getOrCreateRuleSetWrapper(key, type)),
            }).then(wrapper => {
                this.ruleSetWrapperCache.set(key, wrapper);
                this.loadingCategories.delete(key);
            }).catch(() => {
                this.loadingCategories.delete(key);
                this.errorCategories.add(key);
            });
        }
    }

    ngOnDestroy(): void {
        this.subscriptions.forEach(s => s.unsubscribe());
    }

    private filterNodes(nodes: CategoryRead[]): CategoryRead[] {
        return nodes.filter(n => !RulesPageComponent.ILLEGAL_NODES.includes(n.name));
    }

    /** Recursively flatten a tree of categories into a flat sorted list */
    private flattenAndSort(nodes: CategoryRead[]): CategoryRead[] {
        const result: CategoryRead[] = [];
        const recurse = (list: CategoryRead[]) => {
            for (const node of list) {
                result.push(node);
                if (node.children && node.children.length > 0) {
                    recurse(node.children as CategoryRead[]);
                }
            }
        };
        recurse(nodes);
        return result.sort((a, b) => a.qualifiedName.localeCompare(b.qualifiedName));
    }

    /** Split qualifiedName on '#' for display */
    formatQualifiedName(qualifiedName: string): string[] {
        return qualifiedName.split('#');
    }

    get currentFlatCategories(): CategoryRead[] {
        return this.activeView() === 'expenses' ? this.expensesFlatCategories : this.revenueFlatCategories;
    }

    onToggleChange(event: MatButtonToggleChange): void {
        this.activeView.set(event.value as ActiveView);
    }

    /** Load rule set wrapper for a category on-demand */
    loadRuleSetWrapper(category: CategoryRead): void {
        const key = category.qualifiedName;
        if (this.ruleSetWrapperCache.has(key) || this.loadingCategories.has(key)) {
            return;
        }
        this.loadingCategories.add(key);
        this.errorCategories.delete(key);
        const type = this.activeView() === 'expenses'
            ? TransactionTypeEnum.EXPENSES
            : TransactionTypeEnum.REVENUE;

        this.queryClient.fetchQuery({
            queryKey: ['ruleSetWrapper', key, type],
            queryFn: () => firstValueFrom(this.rulesService.getOrCreateRuleSetWrapper(key, type)),
        }).then(wrapper => {
            this.ruleSetWrapperCache.set(key, wrapper);
            this.loadingCategories.delete(key);
        }).catch(() => {
            this.loadingCategories.delete(key);
            this.errorCategories.add(key);
        });
    }

    getRuleSetWrapper(category: CategoryRead): RuleSetWrapperRead | null {
        return this.ruleSetWrapperCache.get(category.qualifiedName) ?? null;
    }

    isLoadingRules(category: CategoryRead): boolean {
        return this.loadingCategories.has(category.qualifiedName);
    }

    hasRuleError(category: CategoryRead): boolean {
        return this.errorCategories.has(category.qualifiedName);
    }

    /** True when the wrapper has been loaded but contains no rules */
    isCategoryEmpty(category: CategoryRead): boolean {
        const wrapper = this.ruleSetWrapperCache.get(category.qualifiedName);
        if (!wrapper) return false; // not loaded yet — don't show chip
        if (!wrapper.ruleSet) return true;
        try {
            const parsed = this.rulesService.parseRuleSet(wrapper);
            return !parsed.rules || parsed.rules.length === 0;
        } catch {
            return true;
        }
    }

    onRetryLoad(category: CategoryRead): void {
        const key = category.qualifiedName;
        const type = this.activeView() === 'expenses'
            ? TransactionTypeEnum.EXPENSES
            : TransactionTypeEnum.REVENUE;
        this.errorCategories.delete(key);
        this.ruleSetWrapperCache.delete(key);
        this.queryClient.removeQueries({queryKey: ['ruleSetWrapper', key, type]});
        this.loadRuleSetWrapper(category);
    }

    onEditRules(category: CategoryRead): void {
        const wrapper = this.getRuleSetWrapper(category);
        if (!wrapper) return;

        const ruleSet = this.rulesService.parseRuleSet(wrapper);
        const data: RuleEditorDialogData = {category, ruleSetWrapper: wrapper, ruleSet};

        const dialogRef = this.dialog.open(RuleEditorDialogComponent, {
            data,
            width: '90vw',
            maxWidth: '900px',
            autoFocus: false,
            ariaLabelledBy: 'rule-editor-title',
        });

        dialogRef.afterClosed().subscribe((result?: RuleSet) => {
            if (result) {
                // Refresh: invalidate cache & re-fetch so the summary card updates
                const key = category.qualifiedName;
                const type = this.activeView() === 'expenses'
                    ? TransactionTypeEnum.EXPENSES
                    : TransactionTypeEnum.REVENUE;
                this.ruleSetWrapperCache.delete(key);
                this.queryClient.removeQueries({queryKey: ['ruleSetWrapper', key, type]});
                this.loadRuleSetWrapper(category);
            }
        });
    }

    onCreateRules(category: CategoryRead): void {
        // Ensure we have a wrapper (get-or-create)
        const existingWrapper = this.getRuleSetWrapper(category);
        if (existingWrapper) {
            // Open with a fresh empty RuleSet
            const emptyRuleSet = new RuleSet('AND', [], false, false);
            const data: RuleEditorDialogData = {
                category,
                ruleSetWrapper: existingWrapper,
                ruleSet: emptyRuleSet,
            };
            const dialogRef = this.dialog.open(RuleEditorDialogComponent, {
                data,
                width: '90vw',
                maxWidth: '900px',
                autoFocus: false,
                ariaLabelledBy: 'rule-editor-title',
            });
            dialogRef.afterClosed().subscribe((result?: RuleSet) => {
                if (result) {
                    const key = category.qualifiedName;
                    const type = this.activeView() === 'expenses'
                        ? TransactionTypeEnum.EXPENSES
                        : TransactionTypeEnum.REVENUE;
                    this.ruleSetWrapperCache.delete(key);
                    this.queryClient.removeQueries({queryKey: ['ruleSetWrapper', key, type]});
                    this.loadRuleSetWrapper(category);
                }
            });
        } else {
            // Load wrapper first, then open dialog
            const type = this.activeView() === 'expenses'
                ? TransactionTypeEnum.EXPENSES
                : TransactionTypeEnum.REVENUE;
            this.queryClient.fetchQuery({
                queryKey: ['ruleSetWrapper', category.qualifiedName, type],
                queryFn: () => firstValueFrom(this.rulesService.getOrCreateRuleSetWrapper(category.qualifiedName, type)),
            }).then(wrapper => {
                this.ruleSetWrapperCache.set(category.qualifiedName, wrapper);
                this.onCreateRules(category); // recurse now that wrapper is loaded
            });
        }
    }

    openRunCategorizationDialog(): void {
        this.dialog.open(RunCategorizationDialogComponent, {
            minWidth: '420px',
            autoFocus: false,
        });
    }
}
