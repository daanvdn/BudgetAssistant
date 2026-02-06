import {Component, inject, OnInit, signal, WritableSignal, OnDestroy} from '@angular/core';
import {CommonModule} from '@angular/common';
import {NestedTreeControl} from '@angular/cdk/tree';
import {
    MatTree,
    MatTreeNestedDataSource,
    MatTreeNodeDef,
    MatTreeNode,
    MatTreeNodeToggle,
    MatNestedTreeNode,
    MatTreeNodeOutlet,
} from '@angular/material/tree';
import {MatToolbar} from '@angular/material/toolbar';
import {MatButtonToggleChange, MatButtonToggleGroup, MatButtonToggle} from '@angular/material/button-toggle';
import {MatButtonModule} from '@angular/material/button';
import {MatIconModule} from '@angular/material/icon';
import {MatTooltipModule} from '@angular/material/tooltip';
import {MatDialog} from '@angular/material/dialog';
import {MatProgressSpinnerModule} from '@angular/material/progress-spinner';
import {Subscription} from 'rxjs';

import {CategoryRead, RuleSetWrapperRead, TransactionTypeEnum} from './rule.models';
import {RulesService} from './rules.service';
import {AppService} from '../app.service';
import {RuleSummaryCardComponent} from './rule-summary-card.component';
import {RunCategorizationDialogComponent} from './run-categorization-dialog.component';

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
        MatTree,
        MatTreeNodeDef,
        MatTreeNode,
        MatTreeNodeToggle,
        MatNestedTreeNode,
        MatTreeNodeOutlet,
        MatProgressSpinnerModule,
        RuleSummaryCardComponent,
    ],
})
export class RulesPageComponent implements OnInit, OnDestroy {
    private appService = inject(AppService);
    private rulesService = inject(RulesService);
    private dialog = inject(MatDialog);

    activeView: WritableSignal<ActiveView> = signal('expenses');

    // Tree controls for both views
    expensesTreeControl = new NestedTreeControl<CategoryRead>(this.getChildren);
    revenueTreeControl = new NestedTreeControl<CategoryRead>(this.getChildren);
    expensesDataSource = new MatTreeNestedDataSource<CategoryRead>();
    revenueDataSource = new MatTreeNestedDataSource<CategoryRead>();

    // Cache of loaded rule set wrappers keyed by category qualifiedName
    ruleSetWrapperCache = new Map<string, RuleSetWrapperRead>();
    loadingCategories = new Set<string>();

    private subscriptions: Subscription[] = [];

    private static readonly ILLEGAL_NODES = ['NO CATEGORY', 'DUMMY CATEGORY'];

    ngOnInit(): void {
        const expSub = this.appService.sharedCategoryTreeExpenses.subscribe(nodes => {
            this.expensesDataSource.data = this.filterAndSort(nodes);
        });

        const revSub = this.appService.sharedCategoryTreeRevenue.subscribe(nodes => {
            this.revenueDataSource.data = this.filterAndSort(nodes);
        });

        this.subscriptions.push(expSub, revSub);
    }

    ngOnDestroy(): void {
        this.subscriptions.forEach(s => s.unsubscribe());
    }

    private filterAndSort(nodes: CategoryRead[]): CategoryRead[] {
        return nodes
            .filter(n => !RulesPageComponent.ILLEGAL_NODES.includes(n.name))
            .sort((a, b) => a.name.localeCompare(b.name));
    }

    private getChildren(node: CategoryRead): CategoryRead[] | undefined {
        const children = node.children;
        return children && children.length > 0 ? children as CategoryRead[] : undefined;
    }

    hasChild = (_: number, node: CategoryRead): boolean => {
        return !!node.children && node.children.length > 0;
    };

    get currentTreeControl(): NestedTreeControl<CategoryRead> {
        return this.activeView() === 'expenses' ? this.expensesTreeControl : this.revenueTreeControl;
    }

    get currentDataSource(): MatTreeNestedDataSource<CategoryRead> {
        return this.activeView() === 'expenses' ? this.expensesDataSource : this.revenueDataSource;
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
        const type = this.activeView() === 'expenses'
            ? TransactionTypeEnum.EXPENSES
            : TransactionTypeEnum.REVENUE;

        this.rulesService.getOrCreateRuleSetWrapper(category.qualifiedName, type).subscribe({
            next: (wrapper) => {
                this.ruleSetWrapperCache.set(key, wrapper);
                this.loadingCategories.delete(key);
            },
            error: () => {
                this.loadingCategories.delete(key);
            },
        });
    }

    getRuleSetWrapper(category: CategoryRead): RuleSetWrapperRead | null {
        return this.ruleSetWrapperCache.get(category.qualifiedName) ?? null;
    }

    isLoadingRules(category: CategoryRead): boolean {
        return this.loadingCategories.has(category.qualifiedName);
    }

    onNodeToggle(node: CategoryRead): void {
        // When expanding a node, load rule sets for all leaf children
        if (this.currentTreeControl.isExpanded(node)) {
            this.loadRuleSetsForBranch(node);
        }
    }

    private loadRuleSetsForBranch(node: CategoryRead): void {
        // Load for the node itself (especially if it's a leaf)
        this.loadRuleSetWrapper(node);
        // Also load for immediate children
        const children = this.getChildren(node);
        if (children) {
            children.forEach(child => this.loadRuleSetWrapper(child));
        }
    }

    onEditRules(category: CategoryRead): void {
        console.log('Edit clicked for:', category.qualifiedName);
    }

    onCreateRules(category: CategoryRead): void {
        console.log('Create clicked for:', category.qualifiedName);
    }

    openRunCategorizationDialog(): void {
        this.dialog.open(RunCategorizationDialogComponent, {
            minWidth: '420px',
            autoFocus: false,
        });
    }
}
