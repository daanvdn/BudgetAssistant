import {SelectionModel} from '@angular/cdk/collections';
import {FlatTreeControl} from '@angular/cdk/tree';
import {
  Component,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  DestroyRef,
  EventEmitter,
  Output,
  ViewChild,
  inject,
  input,
  signal,
  computed,
  effect
} from '@angular/core';
import {takeUntilDestroyed, toObservable} from '@angular/core/rxjs-interop';
import {
  MatTree,
  MatTreeFlatDataSource,
  MatTreeFlattener,
  MatTreeNode,
  MatTreeNodeDef,
  MatTreeNodePadding,
  MatTreeNodeToggle
} from '@angular/material/tree';
import {switchMap, debounceTime} from 'rxjs';
import {AppService} from '../app.service';
import {FormBuilder, FormGroup, FormsModule, ReactiveFormsModule} from '@angular/forms';
import {MatFormField, MatSuffix} from '@angular/material/form-field';
import {MatAutocomplete, MatAutocompleteTrigger} from '@angular/material/autocomplete';
import {FlatCategoryNode, AmountType} from '../model';
import {MatInput} from '@angular/material/input';
import {MatOption} from '@angular/material/core';
import {MatIconButton} from '@angular/material/button';
import {MatCheckbox} from '@angular/material/checkbox';
import {MatIcon} from '@angular/material/icon';
import {TransactionTypeEnum, CategoryRead} from '@daanvdn/budget-assistant-client';

@Component({
  selector: 'app-category-tree-dropdown',
  templateUrl: './category-tree-dropdown.component.html',
  styleUrls: ['./category-tree-dropdown.component.scss'],
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FormsModule,
    ReactiveFormsModule,
    MatFormField,
    MatSuffix,
    MatInput,
    MatAutocompleteTrigger,
    MatAutocomplete,
    MatOption,
    MatTree,
    MatTreeNodeDef,
    MatTreeNode,
    MatTreeNodeToggle,
    MatTreeNodePadding,
    MatIconButton,
    MatCheckbox,
    MatIcon
  ]
})
export class CategoryTreeDropdownComponent {
  private readonly destroyRef = inject(DestroyRef);
  private readonly appService = inject(AppService);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly fb = inject(FormBuilder);

  // --- Signal-based inputs (Angular 18) ---
  readonly transactionTypeEnum = input<TransactionTypeEnum | AmountType>();
  readonly selectedCategoryQualifiedNameStr = input<string | undefined>();

  // --- Output ---
  @Output() selectionChange = new EventEmitter<string>();

  // --- Tree infrastructure ---
  treeControl: FlatTreeControl<FlatCategoryNode>;
  treeFlattener: MatTreeFlattener<CategoryRead, FlatCategoryNode>;
  dataSource: MatTreeFlatDataSource<CategoryRead, FlatCategoryNode>;
  checklistSelection = new SelectionModel<FlatCategoryNode>(false);

  // Maps (rebuilt when data arrives)
  flatNodeMap = new Map<FlatCategoryNode, CategoryRead>();
  nestedNodeMap = new Map<CategoryRead, FlatCategoryNode>();
  qualifiedNameToNodeMap = new Map<string, CategoryRead>();

  // --- Selected state ---
  selectedCategory?: CategoryRead;
  selectedCategoryName = signal<string>('select category');

  // --- Form ---
  categoryFormGroup: FormGroup;

  // --- Raw tree data (for filtering) ---
  private rawTreeData: CategoryRead[] = [];

  @ViewChild('autoCompleteTrigger') autoCompleteTrigger!: MatAutocompleteTrigger;

  // --- Derived: pick the right BehaviorSubject based on transactionTypeEnum ---
  private readonly treeSource$ = computed(() => {
    const type = this.transactionTypeEnum();
    switch (type) {
      case 'REVENUE':
        return this.appService.sharedCategoryTreeRevenue;
      case 'EXPENSES':
        return this.appService.sharedCategoryTreeExpenses;
      default:
        return this.appService.sharedCategoryTree;
    }
  });

  constructor() {
    this.categoryFormGroup = this.fb.group({searchField: ''});

    this.treeFlattener = new MatTreeFlattener(
      this.transformer, this.getLevel, this.isExpandable, this.getChildren
    );
    this.treeControl = new FlatTreeControl<FlatCategoryNode>(this.getLevel, this.isExpandable);
    this.dataSource = new MatTreeFlatDataSource(this.treeControl, this.treeFlattener);

    // React to transactionTypeEnum input changes → subscribe to correct BehaviorSubject
    toObservable(this.treeSource$).pipe(
      switchMap(source$ => source$),
      takeUntilDestroyed(this.destroyRef)
    ).subscribe(data => {
      this.rawTreeData = data;
      this.dataSource.data = data;
      this.restoreSelection();
      this.cdr.markForCheck();
    });

    // Debounced filter on search field
    this.categoryFormGroup.controls['searchField'].valueChanges.pipe(
      debounceTime(150),
      takeUntilDestroyed(this.destroyRef)
    ).subscribe((text: string) => {
      this.applyFilter(text ?? '');
    });

    // React to selectedCategoryQualifiedNameStr input changes
    effect(() => {
      const qn = this.selectedCategoryQualifiedNameStr();
      if (qn) {
        this.restoreSelectionByQualifiedName(qn);
      }
    }, { allowSignalWrites: true });
  }

  // --- Panel lifecycle ---
  onPanelOpened(): void {
    this.cdr.markForCheck();
  }

  onPanelClosed(): void {
    this.categoryFormGroup.controls['searchField'].reset();
    this.dataSource.data = this.rawTreeData;
    this.treeControl.collapseAll();
    this.cdr.markForCheck();
  }

  // --- Clear filter ---
  clearFilter(): void {
    this.categoryFormGroup.controls['searchField'].reset();
    this.dataSource.data = this.rawTreeData;
    this.treeControl.collapseAll();
    this.cdr.markForCheck();
  }

  // --- Tree helpers ---
  transformer = (node: CategoryRead, level: number): FlatCategoryNode => {
    const existingNode = this.nestedNodeMap.get(node);
    const flatNode =
      existingNode && existingNode.qualifiedName === node.qualifiedName
        ? existingNode
        : new FlatCategoryNode();
    flatNode.name = node.name;
    flatNode.nodeId = node.id;
    flatNode.qualifiedName = node.qualifiedName;
    flatNode.level = level;
    flatNode.expandable = (node.children != undefined && node.children.length > 0);
    flatNode.type = node.type as any;
    this.flatNodeMap.set(flatNode, node);
    this.nestedNodeMap.set(node, flatNode);
    this.qualifiedNameToNodeMap.set(node.qualifiedName, node);
    return flatNode;
  };

  getLevel = (node: FlatCategoryNode): number => node.level;

  isExpandable = (node: FlatCategoryNode): boolean => node.expandable;

  getChildren = (node: CategoryRead): CategoryRead[] => {
    const children: CategoryRead[] = [];
    if (node.children && node.children.length > 0) {
      for (const childObj of node.children) {
        children.push(childObj as CategoryRead);
      }
    }
    return children;
  };

  hasChild = (_: number, nodeData: FlatCategoryNode): boolean => nodeData.expandable;

  // --- Selection ---
  toggleSelection(node: FlatCategoryNode): void {
    this.checklistSelection.toggle(node);
    if (this.checklistSelection.isSelected(node)) {
      this.selectedCategory = this.flatNodeMap.get(node);
      this.selectedCategoryName.set(this.selectedCategory?.name ?? 'select category');
      this.selectionChange.emit(this.selectedCategory?.qualifiedName);
    } else {
      this.selectedCategory = undefined;
      this.selectedCategoryName.set('select category');
      this.selectionChange.emit(undefined);
    }
    this.categoryFormGroup.controls['searchField'].reset();
    this.dataSource.data = this.rawTreeData;
    this.autoCompleteTrigger.closePanel();
  }

  // --- Private helpers ---

  /**
   * Attempt to restore the checkbox selection from the current `selectedCategoryQualifiedNameStr` input.
   * Called after tree data arrives.
   */
  private restoreSelection(): void {
    const qn = this.selectedCategoryQualifiedNameStr();
    if (!qn) return;
    this.restoreSelectionByQualifiedName(qn);
  }

  /**
   * Find the node by qualifiedName and select it (without emitting).
   */
  private restoreSelectionByQualifiedName(qualifiedName: string): void {
    const nestedNode = this.qualifiedNameToNodeMap.get(qualifiedName);
    if (!nestedNode) return;
    const flatNode = this.nestedNodeMap.get(nestedNode);
    if (!flatNode) return;

    // Clear previous selection, then select new node
    this.checklistSelection.clear();
    this.checklistSelection.select(flatNode);
    this.selectedCategory = nestedNode;
    this.selectedCategoryName.set(nestedNode.name);
    this.cdr.markForCheck();
  }

  /**
   * Filter the tree based on text input.
   */
  private applyFilter(filterText: string): void {
    if (filterText && filterText.trim().length > 0) {
      const filtered = this.filterTree(this.rawTreeData, filterText);
      this.dataSource.data = filtered;
      this.treeControl.expandAll();
    } else {
      this.dataSource.data = this.rawTreeData;
      this.treeControl.collapseAll();
    }
    this.cdr.markForCheck();
  }

  /**
   * Recursively filter the category tree, keeping nodes whose qualifiedName
   * matches and their ancestor chain.
   */
  private filterTree(nodes: CategoryRead[], text: string): CategoryRead[] {
    const lowerText = text.toLowerCase();
    const getMatching = (result: CategoryRead[], node: CategoryRead): CategoryRead[] => {
      if (node.qualifiedName.toLowerCase().includes(lowerText)) {
        result.push(node);
        return result;
      }
      if (Array.isArray(node.children)) {
        const children = (node.children as CategoryRead[]).reduce(getMatching, []);
        if (children.length) {
          result.push({...node, children} as CategoryRead);
        }
      }
      return result;
    };
    return nodes.reduce(getMatching, []);
  }
}
