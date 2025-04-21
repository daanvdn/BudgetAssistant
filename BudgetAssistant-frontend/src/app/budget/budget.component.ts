import {Component, OnInit} from '@angular/core';
import {AppService} from "../app.service";
import {FlatTreeControl} from "@angular/cdk/tree";
import {MatTreeFlatDataSource, MatTreeFlattener} from "@angular/material/tree";
import {
  AbstractControl,
  FormBuilder,
  FormControl,
  FormGroup,
  FormGroupDirective,
  FormsModule,
  NgForm,
  ReactiveFormsModule,
  ValidatorFn
} from "@angular/forms";
import {ErrorStateMatcher} from '@angular/material/core';
import {MatDialog} from "@angular/material/dialog";
import {SaveErrorDialogComponent} from "./save-error-dialog/save-error-dialog.component";
import {MatToolbar} from '@angular/material/toolbar';
import {BankAccountSelectionComponent} from '../bank-account-selection/bank-account-selection.component';
import {MatButton, MatIconButton} from '@angular/material/button';
import {MatIcon, MatIconModule, MatIconRegistry} from '@angular/material/icon';
import {NgClass, NgIf} from '@angular/common';
import {
  MatCell,
  MatCellDef,
  MatColumnDef,
  MatHeaderCell,
  MatHeaderCellDef,
  MatHeaderRow,
  MatHeaderRowDef,
  MatRow,
  MatRowDef,
  MatTable
} from '@angular/material/table';
import {MatError, MatFormField} from '@angular/material/form-field';
import {MatInput} from '@angular/material/input';
import {HttpResponse} from "@angular/common/http";

export interface BudgetTreeNode {
  budgetTreeNodeAmount: number;
  budgetTreeNodeId: number;
  budgetTreeNodeParentId: number;
  children: BudgetTreeNode[];
  name: string;
  qualifiedName: string;
}

export class FlatBudgetTreeNode {
  level!: number;
  expandable!: boolean;
  name!: string;
  qualifiedName!: string;
  budgetTreeNodeId!: number;
  budgetTreeNodeAmount!: number;
  budgetTreeNodeParentId!: number;
}



export interface FindOrCreateBudgetResponse {
  response: string;
  failureReason: string | undefined | null;
  errorMessage: string | undefined | null;
  budgetTreeNodes: BudgetTreeNode[];
  numberOfBudgetTreeNodes: number;

}

export interface UpdateBudgetEntryResponse {
  response: string;
  failureReason: string | undefined | null;
  errorMessage: string | undefined | null;


}


export class MyErrorStateMatcher implements ErrorStateMatcher {
  isErrorState(control: FormControl | null, form: FormGroupDirective | NgForm | null): boolean {
    return !!(control && control.invalid);
  }
}


@Component({
    selector: 'app-budget',
    templateUrl: './budget.component.html',
    styleUrls: ['./budget.component.scss'],
    standalone: true,
  imports: [MatToolbar, BankAccountSelectionComponent,
    MatButton, MatIcon, NgIf, FormsModule, ReactiveFormsModule, MatTable, MatColumnDef, MatHeaderCellDef, MatHeaderCell,
    MatCellDef, MatCell, MatIconButton, MatFormField, MatInput, MatError, MatHeaderRowDef,
    MatHeaderRow, MatRowDef, MatRow, NgClass, MatIconModule, MatIcon],

})
export class BudgetComponent implements OnInit {
  TOTAL_NODE_ID: number = -1;
  TOTAL_NODE_CATEGORY_NAME = 'Totaal';

  totalBudget: number = 0;

  matcher = new MyErrorStateMatcher();


  /** Map from flat node to nested node. This helps us finding the nested node to be modified */
  idToNodeMap = new Map<number, BudgetTreeNode>();

  /** Map from nested node to flattened node. This helps us to keep the same object for selection */
  nestedNodeMap = new Map<BudgetTreeNode, FlatBudgetTreeNode>();

  qualifiedNameToNodeMap = new Map<string, BudgetTreeNode>();

  treeControl!: FlatTreeControl<FlatBudgetTreeNode>
  dataSource!: MatTreeFlatDataSource<BudgetTreeNode, FlatBudgetTreeNode>;


  treeFlattener: MatTreeFlattener<BudgetTreeNode, FlatBudgetTreeNode>;

  displayedColumns: string[] = ['category', 'budget', 'yearlyBudget'];

  rowsToHighlight: Set<number> = new Set<number>();

  idToControlsMap: Map<number, FormControl> = new Map<number, FormControl>();
  controlsToIdMap: Map<FormControl, number> = new Map<FormControl, number>();
  allControls: FormControl[] = [];
  mainForm: FormGroup;
  idToBudgetNodeMap: Map<number, BudgetTreeNode> = new Map<number, BudgetTreeNode>();
  currentSubTreeHasError: boolean = false;
  isTreeExpanded = true;


  constructor(private appService: AppService, private fb: FormBuilder, public dialog: MatDialog
  ) {

    this.mainForm = this.fb.group({});

    this.treeFlattener = new MatTreeFlattener(
      this.transformer,
      this.getLevel,
      this.isExpandable,
      this.getChildren
    );
    this.treeControl = new FlatTreeControl<FlatBudgetTreeNode>(
      this.getLevel,
      this.isExpandable
    );
    this.dataSource = new MatTreeFlatDataSource<BudgetTreeNode, FlatBudgetTreeNode>(
      this.treeControl,
      this.treeFlattener
    );



  }


  transformer = (node: BudgetTreeNode, level: number) => {
    const existingNode = this.nestedNodeMap.get(node);
    const flatNode =
      existingNode && existingNode.qualifiedName === node.qualifiedName
        ? existingNode
        : new FlatBudgetTreeNode();
    flatNode.name = node.name;
    flatNode.qualifiedName = node.qualifiedName;
    flatNode.level = level;
    flatNode.expandable = (node.children != undefined && node.children.length > 0);
    flatNode.budgetTreeNodeAmount = node.budgetTreeNodeAmount;
    flatNode.budgetTreeNodeId = node.budgetTreeNodeId;
    flatNode.budgetTreeNodeParentId = node.budgetTreeNodeParentId;
    this.idToNodeMap.set(node.budgetTreeNodeId, node);

    this.nestedNodeMap.set(node, flatNode);
    this.qualifiedNameToNodeMap.set(node.qualifiedName, node);
    return flatNode;
  };

  getLevel = (node: FlatBudgetTreeNode) => node.level;

  isExpandable = (node: FlatBudgetTreeNode) => node.expandable;

  getChildren = (node: BudgetTreeNode): BudgetTreeNode[] => node.children;

  hasChild = (_: number, _nodeData: FlatBudgetTreeNode) => _nodeData.expandable;

  inputChanged: boolean = false;
  dataLoaded: boolean = false;
  isSaved: boolean = false;


  getRowClass(data: FlatBudgetTreeNode): string {
    if (data.name === this.TOTAL_NODE_CATEGORY_NAME) {
      return 'highlight-total-row';
    }
    if (this.currentSubTreeHasError && this.sameSubTreeAsFocusedBudgetNode(data)) {
      return 'highlight-row-error';
    }
    if (this.sameSubTreeAsFocusedBudgetNode(data)) {
      return 'highlight-row-no-error';
    }
    return '';
  }


  ngOnInit(): void {
    this.appService.selectedBankAccountObservable$.subscribe(selectedAccount => {
      if (selectedAccount) {
        this.appService.findOrCreateBudget(selectedAccount).subscribe((response: BudgetTreeNode[]) => {

          let filteredData = response.filter(node => node.name !== 'NO CATEGORY' && node.name !== 'DUMMY CATEGORY');
          let totalBudgetTreeNode = this.initTotalBudgetTreeNode();
          filteredData.push(totalBudgetTreeNode);
          this.dataSource.data = filteredData;
          let allBudgetNodes: BudgetTreeNode[] = [];
          for (const node of response) {
            if (node.name === 'NO CATEGORY' || node.name === 'DUMMY CATEGORY') {
              continue;
            }
            allBudgetNodes.push(node);
            this.getAllDescendantsRecursively(node, allBudgetNodes);
          }


          for (const node of allBudgetNodes) {
            this.idToBudgetNodeMap.set(node.budgetTreeNodeId, node);
            let control = new FormControl<number>(node.budgetTreeNodeAmount, [this.budgetValidator(), this.negativeNumberValidator()]);
            this.idToControlsMap.set(node.budgetTreeNodeId, control);
            control.valueChanges.subscribe((value) => {
              if ((value !== undefined)) {
                // this.inputChanged = false;
                this.validateAllControls();
                this.calculateTotalBudget();

                let flatNode = this.nestedNodeMap.get(node);
                if (flatNode){
                  if (flatNode.name === this.TOTAL_NODE_CATEGORY_NAME) {
                    //we don't want to do anything when the total node is changed
                    return;
                  }
                  this.determineSubTreeForNode(flatNode as FlatBudgetTreeNode);
                  if (!this.currentSubTreeHasError){
                    this.onBudgetChange(flatNode as FlatBudgetTreeNode);
                  }
                }
              }
            });
            this.idToBudgetNodeMap.set(node.budgetTreeNodeId, node);
            this.controlsToIdMap.set(control, node.budgetTreeNodeId);
            this.allControls.push(control);
            this.mainForm.addControl(node.budgetTreeNodeId.toString(), control);
          }
          this.calculateTotalBudget();
          this.dataLoaded = true;
          this.treeControl.expandAll();

        });
      }
    });

  }

  getDescendantIds(node: BudgetTreeNode, allDescendantIds: number[]) {
    if (node.children && node.children.length > 0) {
      node.children.forEach(child => {
        allDescendantIds.push(child.budgetTreeNodeId);
        this.getDescendantIds(child, allDescendantIds);
      });
    }
  }

  validateAllControls() {
    Object.keys(this.mainForm.controls).forEach(key => {
      const control = this.mainForm.get(key);
      if (control) {
        control.updateValueAndValidity({onlySelf: false, emitEvent: false});

      }
    });
    this.mainForm.markAllAsTouched();
  }

  budgetValidator(): ValidatorFn {
    return (control: AbstractControl): { [key: string]: any } | null => {
      const isLessThanSumOfDescendants = this.isLessThanSumOfDescendants(control as FormControl);
      return isLessThanSumOfDescendants ? {'isLessThanItsDescendants': {value: control.value}} : null;
    };
  }

  negativeNumberValidator(): ValidatorFn {
    return (control: AbstractControl): { [key: string]: any } | null => {
      const isNegative = control.value < 0;
      return isNegative ? {'negativeNumber': {value: control.value}} : null;
    };
  }

  isLessThanSumOfDescendants(control: FormControl): boolean {
    let nodeId = this.controlsToIdMap.get(control);
    if (!nodeId) {
      return false;
    }

    let nodeValue = control.value;

    if (nodeValue == undefined || nodeValue < 0) {
      return false;
    }
    let sumOfDescendants = 0;

    let payload = this.idToBudgetNodeMap.get(nodeId) as BudgetTreeNode;
    let allDescendantIds: number[] = [];
    this.getDescendantIds(payload, allDescendantIds);

    for (const descendantId of allDescendantIds) {
      let descendantValue = this.idToControlsMap.get(descendantId)?.value;
      if (descendantValue) {
        sumOfDescendants = sumOfDescendants + descendantValue;

      }
    }


    let isLessThanSumOfDescendants = nodeValue < sumOfDescendants;
    //unpacking boolean for debugging purposes
    return isLessThanSumOfDescendants;

  }


  determineSubTreeForNode(data: FlatBudgetTreeNode) {
    this.rowsToHighlight = new Set<number>();
    this.currentSubTreeHasError = false;
    let budgetTreeNode = this.idToNodeMap.get(data.budgetTreeNodeId);
    if (budgetTreeNode == undefined) {
      return;
    }
    this.rowsToHighlight.add(budgetTreeNode.budgetTreeNodeId);
    if (budgetTreeNode.budgetTreeNodeParentId) {
      //go one level up the tree to the parent. Add the id of the parent and all its descendants to the set of rows to highlight
      this.rowsToHighlight.add(budgetTreeNode.budgetTreeNodeParentId);
      let parentBudgetTreeNode = this.idToNodeMap.get(budgetTreeNode.budgetTreeNodeParentId);
      if (parentBudgetTreeNode == undefined) {
        return;
      }

      let allDescendantIds: number[] = [];
      this.getDescendantIds(parentBudgetTreeNode, allDescendantIds);
      allDescendantIds.forEach(id => {
        this.rowsToHighlight.add(id);
      });



    } else {
      let allDescendantIds: number[] = [];
      this.getDescendantIds(budgetTreeNode, allDescendantIds);
      this.rowsToHighlight.add(budgetTreeNode.budgetTreeNodeId);
      allDescendantIds.forEach(id => {
        this.rowsToHighlight.add(id);
      });
    }
    this.currentSubTreeHasError = this.anyFormControlIsInvalid(this.rowsToHighlight);


  }

  private anyFormControlIsInvalid(ids: Set<number>): boolean {
    let idsArray = [...ids];
    for (const number of idsArray) {
      if(this.formControlIsInvalid(number)){
        return true;
      }
    }

    return false;




  }

  private formControlIsInvalid(budgetTreeNodeId: number): boolean {
    let control = this.mainForm.get(budgetTreeNodeId.toString());
    if (control) {
      return control.invalid;
    }
    return false;
  }


  /*onBlur() {
    this.inputChanged = true;
  }

  onKeyUpEnter(event: Event) {
    let kbe = event as KeyboardEvent;
    if (kbe.key === 'Enter') {
      this.inputChanged = true;
    }
  }*/

  getAllDescendantsRecursively(budgetTreeNode: BudgetTreeNode, descendants: BudgetTreeNode[]) {
    if (budgetTreeNode.children && budgetTreeNode.children.length > 0) {
      budgetTreeNode.children.forEach(child => {
        descendants.push(child);
        this.getAllDescendantsRecursively(child, descendants);
      });
    }
  }




  onBudgetChange(data: FlatBudgetTreeNode): void {

    let budgetControl = this.mainForm.get(data.budgetTreeNodeId.toString()) as FormControl;
    if (budgetControl == undefined) {
      return;
    }
    if (data.budgetTreeNodeAmount === undefined || data.budgetTreeNodeAmount === null) {
      data.budgetTreeNodeAmount = 0;
      budgetControl.setValue(0);
    }


    if (!budgetControl.valid) {
      return;
    }
    let budgetTreeNode = this.idToNodeMap.get(data.budgetTreeNodeId);
    if (budgetTreeNode == undefined) {
      return;
    }


    if (budgetTreeNode.budgetTreeNodeAmount !== budgetControl.value) {
      budgetTreeNode.budgetTreeNodeAmount = budgetControl.value;
    }

    this.appService.
    updateBudgetEntryAmount(budgetTreeNode).subscribe(
      (
        response: HttpResponse<any>
      ) => {
        if (!response.ok) {
          throw new Error("Failed to update budget entry amount");
        }
        // this.recalculateCumulatedAmountsForAllNodes();
        this.treeControl.expandAll();
      });

  }

  sameSubTreeAsFocusedBudgetNode(data: FlatBudgetTreeNode): boolean {
    return this.rowsToHighlight.has(data.budgetTreeNodeId);

  }


  /*onInputChange() {
    this.inputChanged = true
  }*/

  saveAll() {
    if (this.mainForm.invalid) {
      let invalidCategories: BudgetTreeNode[] = [];
      Object.keys(this.mainForm.controls).forEach(key => {
        const control = this.mainForm.get(key);
        if (control && control.invalid) {
          let node = this.idToNodeMap.get(parseInt(key));
          if (!node) {
            throw new Error("Failed to find node for id " + key);
          }
          node.budgetTreeNodeAmount = control.value;
          invalidCategories.push(node);


        }
      });
      this.dialog.open(SaveErrorDialogComponent, {
        data: {
          message: 'Sommige wijzingen kunnen niet worden opgeslaan! Corrigeer de inconsistente budgetbedragen voor onderstaande categorieën en probeer opnieuw:',
          nodes: invalidCategories
        }
      });
    } else {
      let budgetTreeNodes = this.dataSource.data;
      for (const budgetTreeNode of budgetTreeNodes) {
        if (budgetTreeNode.budgetTreeNodeId === this.TOTAL_NODE_ID) {
          continue;
        }
        let flatNode = this.nestedNodeMap.get(budgetTreeNode);
        if (!flatNode) {
          throw new Error("Failed to find flat node for budget tree node " + budgetTreeNode);
        } else {
          this.onBudgetChange(flatNode);
        }


      }






    }
  }


  toggleTree(): void {
    if (this.isTreeExpanded) {
      this.treeControl.collapseAll();
    } else {
      this.treeControl.expandAll();
    }
    this.isTreeExpanded = !this.isTreeExpanded;
  }

  calculateTotalBudget(): void {
    this.totalBudget = Array.from(this.idToControlsMap.values()).filter(control => control.valid)
      .reduce((sum, control) => sum + (control.value || 0), 0);
    let totalNode = {
      budgetTreeNodeAmount: this.totalBudget,
      budgetTreeNodeId: this.TOTAL_NODE_ID, // Use a unique ID that does not conflict with existing IDs
      budgetTreeNodeParentId: -1,
      children: [],
      name: this.TOTAL_NODE_CATEGORY_NAME,
      qualifiedName: this.TOTAL_NODE_CATEGORY_NAME
    };
    this.dataSource.data = [totalNode, ...this.dataSource.data.slice(1, this.dataSource.data.length - 1), totalNode];
    this.mainForm.get(totalNode.budgetTreeNodeId.toString())?.setValue(totalNode.budgetTreeNodeAmount);
  }

  initTotalBudgetTreeNode(): BudgetTreeNode {
    return {
      budgetTreeNodeAmount: 0,
      budgetTreeNodeId: this.TOTAL_NODE_ID, // Use a unique ID that does not conflict with existing IDs
      budgetTreeNodeParentId: -1,
      children: [],
      name: this.TOTAL_NODE_CATEGORY_NAME,
      qualifiedName: this.TOTAL_NODE_CATEGORY_NAME
    };
  }

}


