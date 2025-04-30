import {NestedTreeControl} from '@angular/cdk/tree';
import {Component, Inject, OnInit} from '@angular/core';
import {AppService} from "../app.service";
import {
    MatTreeNestedDataSource,
    MatTree,
    MatTreeNodeDef,
    MatTreeNode,
    MatTreeNodeToggle,
    MatNestedTreeNode,
    MatTreeNodeOutlet
} from "@angular/material/tree";
import {faNetworkWired, faPlay} from "@fortawesome/free-solid-svg-icons";
import {MatButtonToggleChange, MatButtonToggleGroup, MatButtonToggle} from "@angular/material/button-toggle";
import {
    MAT_DIALOG_DATA,
    MatDialog,
    MatDialogRef,
    MatDialogTitle,
    MatDialogContent,
    MatDialogActions
} from "@angular/material/dialog";
import {ActiveView, TransactionsCategorizationResponse} from "../model";
import {ErrorDialogService} from "../error-dialog/error-dialog.service";
import {AuthService} from "../auth/auth.service";
import {faSearch} from "@fortawesome/free-solid-svg-icons/faSearch";
import {MatToolbar} from '@angular/material/toolbar';
import {MatIconButton, MatButton} from '@angular/material/button';
import {FaIconComponent} from '@fortawesome/angular-fontawesome';
import {MatTooltip} from '@angular/material/tooltip';
import {NgSwitch, NgSwitchCase} from '@angular/common';
import {MatIcon} from '@angular/material/icon';
import {RulesBuilderComponent} from '../rules-builder/rules-builder.component';
import {CdkScrollable} from '@angular/cdk/scrolling';
import {SimplifiedCategory} from '@daanvdn/budget-assistant-client'

@Component({
    selector: 'app-dialog', templateUrl: './run-categorization-dialog-component.component.html',
    standalone: true,
    imports: [
        MatDialogTitle,
        CdkScrollable,
        MatDialogContent,
        MatDialogActions,
        MatButton,
    ],
})
export class RunCategorizationDialogComponent {

    constructor(public dialogRef: MatDialogRef<RunCategorizationDialogComponent>,
                @Inject(MAT_DIALOG_DATA) public data: TransactionsCategorizationResponse) {
    }

    onOkClick(): void {
        this.dialogRef.close();
    }

}

@Component({
    selector: 'app-expenses-rules-view',
    templateUrl: './rules-view.component.html',
    styleUrls: ['./rules-view.component.scss'],
    standalone: true,
    imports: [MatToolbar, MatIconButton, FaIconComponent, MatTooltip, NgSwitch, NgSwitchCase, MatButtonToggleGroup, MatButtonToggle, MatTree, MatTreeNodeDef, MatTreeNode, MatTreeNodeToggle, MatIcon, MatNestedTreeNode, MatTreeNodeOutlet, MatButton, RulesBuilderComponent]
})
export class RulesViewComponent implements OnInit {

    activeView: ActiveView = ActiveView.EXPENSES;
    expensesCategoryWrapper!: CategoryTreeWrapper;
    revenueCategoryTreeWrapper!: CategoryTreeWrapper;

    selectedCategoryNode!: SimplifiedCategory;


    showCategoryTree: boolean = true;


    constructor(private appService: AppService, public dialog: MatDialog,
                private errorDialogService: ErrorDialogService, private authService: AuthService) {
    }


    onClickCreateRule(node: SimplifiedCategory) {
        this.selectedCategoryNode = node;
        this.showCategoryTree = false;
    }

    ngOnInit(): void {
        this.expensesCategoryWrapper = new CategoryTreeWrapper(this.appService, "expenses");
        this.revenueCategoryTreeWrapper = new CategoryTreeWrapper(this.appService, "revenue");
    }

    hasChild = (_: number, node: SimplifiedCategory) => !!node.children && node.children.length > 0;


    protected readonly faNetworkWired = faNetworkWired;
    protected readonly faPlay = faPlay;


    getTooltip(node: any): string {
        let qualifiedName = (node as SimplifiedCategory).qualifiedName;
        return `create rule for category ${qualifiedName}`

    }

    onToggleChange($event: MatButtonToggleChange) {
        const value = $event.value;
        if (value === "expenses") {
            this.activeView = ActiveView.EXPENSES;
        }
        else if (value === "revenue") {
            this.activeView = ActiveView.REVENUE;
        }
        else {
            throw new Error("Unknown value " + value);
        }
    }

    protected readonly ActiveView = ActiveView;

    onClickNavigateBackToCategories() {
        this.showCategoryTree = true;
    }

    runRules() {
        try {
            let user = this.authService.getUser();
            if (!user || !user.userName) {
                this.errorDialogService.openErrorDialog("Cannot run rules", "User is not defined!");
                return;
            }

            this.appService.categorizeTransactions(user.userName).subscribe(response => {
                    this.openDialog(response);
                },

                error => {
                    this.errorDialogService.openErrorDialog("Error running categorization", error.message)
                })
        } catch (e) {

            this.errorDialogService.openErrorDialog("Error running categorization", (e as Error).message);
        }
    }

    openDialog(data: TransactionsCategorizationResponse): void {
        const dialogRef = this.dialog.open(RunCategorizationDialogComponent, {
            minWidth: '400px', data: data
        });


    }


    protected readonly faSearch = faSearch;
}

function doGetChildren(node: SimplifiedCategory): Array<SimplifiedCategory> | undefined {
    let children = node.children;
    if (children && children.length > 0) {
        return children as unknown as Array<SimplifiedCategory>;
    }
    return undefined;
}

class CategoryTreeWrapper {


    treeControl = new NestedTreeControl<SimplifiedCategory>(doGetChildren);


    dataSource = new MatTreeNestedDataSource<SimplifiedCategory>();


    constructor(private appService: AppService, type: string) {
        const illegalNodes = ["NO CATEGORY", "DUMMY CATEGORY"]

        const filterAndSortNodes = (nodes: SimplifiedCategory[]) => {
            return nodes.filter(n => !illegalNodes.includes(n.name)).sort((a, b) => a.name.localeCompare(b.name));
        }


        switch (type) {
            case "revenue":
                this.appService.sharedCategoryTreeRevenueObservable$.subscribe(nodes => {
                    this.dataSource.data = filterAndSortNodes(nodes);
                })
                break;
            case "expenses":
                this.appService.sharedCategoryTreeExpensesObservable$.subscribe(nodes => {
                    this.dataSource.data = filterAndSortNodes(nodes);
                })
                break;
            default:
                throw new Error("Unknown type " + type + "!");
        }
    }
}
