import {SelectionModel} from '@angular/cdk/collections';
import {FlatTreeControl} from '@angular/cdk/tree';
import {Component, EventEmitter, Input, OnInit, Output, ViewChild} from '@angular/core';
import { MatTreeFlatDataSource, MatTreeFlattener, MatTree, MatTreeNodeDef, MatTreeNode, MatTreeNodeToggle, MatTreeNodePadding } from '@angular/material/tree';
import {BehaviorSubject} from 'rxjs';
import {AppService} from '../app.service';
import { FormBuilder, FormGroup, FormsModule, ReactiveFormsModule } from "@angular/forms";
import {MatFormField} from "@angular/material/form-field";
import { MatAutocompleteTrigger, MatAutocomplete } from "@angular/material/autocomplete";
import {AmountType, CategoryNode, FlatCategoryNode, NO_CATEGORY} from "../model";
import { MatInput } from '@angular/material/input';
import { MatOption } from '@angular/material/core';
import { MatIconButton } from '@angular/material/button';
import { MatCheckbox } from '@angular/material/checkbox';
import { MatIcon } from '@angular/material/icon';


// @Injectable({ providedIn: "root" })
export class BackingDatabase {
  dataChange = new BehaviorSubject<CategoryNode[]>([]);
  treeData?: any[];

  get data(): CategoryNode[] {
    return this.dataChange.value;
  }

  constructor(private appService: AppService, amountType: AmountType) {
    this.initialize(amountType);
  }



  initialize(amountType: AmountType) {

    switch (amountType) {
      case AmountType.REVENUE:
        this.appService.sharedCategoryTreeRevenueObservable$.subscribe(tree => {
          this.treeData = tree;
          // Build the tree nodes from Json object. The result is a list of `TodoItemNode` with nested
          //     file node as children.
          const data = tree;

          // Notify the change.
          this.dataChange.next(data);

        });
        break;
      case AmountType.EXPENSES:
        this.appService.sharedCategoryTreeExpensesObservable$.subscribe(tree => {
          this.treeData = tree;
          // Build the tree nodes from Json object. The result is a list of `TodoItemNode` with nested
          //     file node as children.
          const data = tree;

          // Notify the change.
          this.dataChange.next(data);

        });
        break;
      case AmountType.BOTH:


        this.appService.sharedCategoryTreeObservable$?.subscribe(tree => {
          this.treeData = tree;
          // Build the tree nodes from Json object. The result is a list of `TodoItemNode` with nested
          //     file node as children.
          const data = tree;

          // Notify the change.
          this.dataChange.next(data);

        });
        break;

    }





  }

  public filter(filterText: string) {
    let filteredTreeData;
    if (filterText && filterText.trim().length > 0) {
      // Filter the tree
      function filter(array: any, text: any) {
        const getChildren = (result: any[], object: { qualifiedName: string; children: any[]; }) => {

          if (object.qualifiedName.toLowerCase() === text.toLowerCase() || object.qualifiedName.toLowerCase().includes(text.toLowerCase())) {
            result.push(object);
            return result;
          }
          if (Array.isArray(object.children)) {
            const children = object.children.reduce(getChildren, []);
            if (children.length) result.push({ ...object, children });
          }
          return result;
        };

        return array.reduce(getChildren, []);
      }

      filteredTreeData = filter(this.treeData, filterText);
    } else {
      // Return the initial tree
      filteredTreeData = this.treeData;
    }

    // Build the tree nodes from Json object. The result is a list of `TodoItemNode` with nested
    // file node as children.
    const data = filteredTreeData;
    // Notify the change.
    this.dataChange.next(data);
  }
}




@Component({
    selector: 'app-category-tree-dropdown',
    templateUrl: './category-tree-dropdown.component.html',
    styleUrls: ['./category-tree-dropdown.component.scss'],
    standalone: true,
    imports: [FormsModule, ReactiveFormsModule, MatFormField, MatInput, MatAutocompleteTrigger, MatAutocomplete, MatOption, MatTree, MatTreeNodeDef, MatTreeNode, MatTreeNodeToggle, MatTreeNodePadding, MatIconButton, MatCheckbox, MatIcon]
})
export class CategoryTreeDropdownComponent implements OnInit  {

  /** Map from flat node to nested node. This helps us finding the nested node to be modified */
  flatNodeMap = new Map<FlatCategoryNode, CategoryNode>();

  /** Map from nested node to flattened node. This helps us to keep the same object for selection */
  nestedNodeMap = new Map<CategoryNode, FlatCategoryNode>();

  qualifiedNameToNodeMap = new Map<string, CategoryNode>();

  @Input()
  selectedCategoryQualifiedNameStr?: string;
  selectedCategory?: CategoryNode;
  selectedCategoryName?: string = "select category"
  // treeControl = new NestedTreeControl<CategoryNode>(node => node.children);
  treeControl!: FlatTreeControl<FlatCategoryNode>
  dataSource!: MatTreeFlatDataSource<CategoryNode, FlatCategoryNode>;
  @Input()
  amountType?: AmountType;

  @Output() selectionChange: EventEmitter<string> = new EventEmitter<string>();

  @ViewChild('formField') formField!: MatFormField;
  @ViewChild('autoCompleteTrigger') autoCompleteTrigger!: MatAutocompleteTrigger;




  treeFlattener: MatTreeFlattener<CategoryNode, FlatCategoryNode>;

  /** The selection for checklist */
  checklistSelection = new SelectionModel<FlatCategoryNode>(false /* multiple */);
  _database?: BackingDatabase;

  constructor(private appService: AppService, private formBuilder: FormBuilder) {
    this.categoryFormGroup = this.formBuilder.group({
      queryForm: "", searchField: ""
    });
    this.treeFlattener = new MatTreeFlattener(
      this.transformer,
      this.getLevel,
      this.isExpandable,
      this.getChildren
    );
    this.treeControl = new FlatTreeControl<FlatCategoryNode>(
      this.getLevel,
      this.isExpandable
    );
    this.dataSource = new MatTreeFlatDataSource(
      this.treeControl,
      this.treeFlattener
    );

  }



  ngOnInit(): void {

    if (this.selectedCategoryQualifiedNameStr !== undefined) {
      this.selectedCategory = this.qualifiedNameToNodeMap.get(this.selectedCategoryQualifiedNameStr);
      if (this.selectedCategory !== undefined) {
        let flatNode = this.nestedNodeMap.get(this.selectedCategory);
        if (flatNode !== undefined) {
          this.toggleSelectionWithoutEmittingChange(flatNode);

        }
      }

    }
    if (this.amountType !== undefined) {
      this._database = new BackingDatabase(this.appService, this.amountType);
      this._database.dataChange.subscribe(data => {
        this.dataSource.data = data;
      });
    }


  }


  transformer = (node: CategoryNode, level: number) => {
    const existingNode = this.nestedNodeMap.get(node);
    const flatNode =
      existingNode && existingNode.qualifiedName === node.qualifiedName
        ? existingNode
        : new FlatCategoryNode();
    flatNode.name = node.name;
    flatNode.qualifiedName = node.qualifiedName;
    flatNode.level = level;
    flatNode.expandable = (node.children != undefined && node.children.length > 0);
    flatNode.type = node.type;
    this.flatNodeMap.set(flatNode, node);
    this.nestedNodeMap.set(node, flatNode);
    this.qualifiedNameToNodeMap.set(node.qualifiedName, node);
    return flatNode;
  };

  getLevel = (node: FlatCategoryNode) => node.level;

  isExpandable = (node: FlatCategoryNode) => node.expandable;

  getChildren = (node: CategoryNode): CategoryNode[] => node.children;

  hasChild = (_: number, _nodeData: FlatCategoryNode) => _nodeData.expandable;

  hasNoContent = (_: number, _nodeData: FlatCategoryNode) => _nodeData.name === "";
  categoryFormGroup: FormGroup;

  filterChanged(event: Event) {

    let filterText: string = (<HTMLInputElement>(event as InputEvent).target).value
    // ChecklistDatabase.filter method which actually filters the tree and gives back a tree structure
    this._database?.filter(filterText);
    if (filterText) {
      this.treeControl.expandAll();
    } else {
      this.treeControl.collapseAll();
    }
  }

  toggleSelection(node: FlatCategoryNode): void {
    this.checklistSelection.toggle(node);
    if(this.checklistSelection.isSelected(node)){
      this.selectedCategory = this.flatNodeMap.get(node);
      this.selectedCategoryQualifiedNameStr = this.selectedCategory?.qualifiedName;
      this.selectedCategoryName = this.selectedCategory?.name;
      this.selectionChange.emit(this.selectedCategoryQualifiedNameStr);
    } else{
      this.selectedCategory = NO_CATEGORY;
      this.selectedCategoryQualifiedNameStr = this.selectedCategory?.qualifiedName;
      this.selectedCategoryName = "selecteer categorie";
      this.selectionChange.emit(this.selectedCategoryQualifiedNameStr);
    }
    this.categoryFormGroup.controls['searchField'].reset();
    this._database?.filter("")
    this.autoCompleteTrigger.closePanel();

  }
  toggleSelectionWithoutEmittingChange(node: FlatCategoryNode): void {
    this.checklistSelection.toggle(node);
    if(this.checklistSelection.isSelected(node)){
      this.selectedCategory = this.flatNodeMap.get(node);
      this.selectedCategoryQualifiedNameStr = this.selectedCategory?.qualifiedName;
      this.selectedCategoryName = this.selectedCategory?.name;
    } else {
      this.selectedCategory = NO_CATEGORY;
      this.selectedCategoryQualifiedNameStr = this.selectedCategory?.qualifiedName;
      this.selectedCategoryName = "selecteer categorie";
    }

  }









}
