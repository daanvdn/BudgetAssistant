import {NestedTreeControl} from '@angular/cdk/tree';
import {Component, Inject, OnInit} from '@angular/core';
import {AppService} from "../app.service";
import {MatTreeNestedDataSource} from "@angular/material/tree";
import {faNetworkWired, faPlay} from "@fortawesome/free-solid-svg-icons";
import {MatButtonToggleChange} from "@angular/material/button-toggle";
import {MAT_DIALOG_DATA, MatDialog, MatDialogRef} from "@angular/material/dialog";
import {ActiveView, CategoryNode, TransactionsCategorizationResponse} from "../model";
import {ErrorDialogService} from "../error-dialog/error-dialog.service";
import {AuthService} from "../auth/auth.service";
import {faSearch} from "@fortawesome/free-solid-svg-icons/faSearch";


@Component({
  selector: 'app-dialog', templateUrl: './run-categorization-dialog-component.component.html',
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
  styleUrls: ['./rules-view.component.scss']
})
export class RulesViewComponent implements OnInit {

  activeView: ActiveView = ActiveView.EXPENSES;
  expensesCategoryWrapper!: CategoryTreeWrapper;
  revenueCategoryTreeWrapper!: CategoryTreeWrapper;

  selectedCategoryNode!: CategoryNode;


  showCategoryTree: boolean = true;


  constructor(private appService: AppService, public dialog: MatDialog,
              private errorDialogService: ErrorDialogService, private authService: AuthService){
  }


  onClickCreateRule(node: CategoryNode){
    this.selectedCategoryNode = node;
    this.showCategoryTree= false;
  }

  ngOnInit(): void {
    this.expensesCategoryWrapper = new CategoryTreeWrapper(this.appService, "expenses");
    this.revenueCategoryTreeWrapper = new CategoryTreeWrapper(this.appService, "revenue");
  }

  hasChild = (_: number, node: CategoryNode) => !!node.children && node.children.length > 0;


  protected readonly faNetworkWired = faNetworkWired;
  protected readonly faPlay = faPlay;


  getTooltip(node: any): string {
    let qualifiedName = (node as CategoryNode).qualifiedName;
    return `create rule for category ${qualifiedName}`

  }

  onToggleChange($event: MatButtonToggleChange) {
    const value = $event.value;
    if (value === "expenses") {
      this.activeView = ActiveView.EXPENSES;
    } else if (value === "revenue") {
      this.activeView = ActiveView.REVENUE;
    } else {
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
      if (!user ||!user.userName) {
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

  onChangeSelectedBankAccountsForCurrentRule($event: string[]) {

  }

  protected readonly faSearch = faSearch;
}


class CategoryTreeWrapper {

  treeControl = new NestedTreeControl<CategoryNode>(node => node.children);
  dataSource = new MatTreeNestedDataSource<CategoryNode>();


  constructor(private appService: AppService, type: string) {
    const illegalNodes = ["NO CATEGORY", "DUMMY CATEGORY"]

    const filterAndSortNodes = (nodes: CategoryNode[]) => {
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
