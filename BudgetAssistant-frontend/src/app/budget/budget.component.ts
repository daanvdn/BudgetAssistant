import {Component, computed, DestroyRef, effect, inject, OnInit, signal} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {FlatTreeControl} from '@angular/cdk/tree';
import {MatTreeFlatDataSource, MatTreeFlattener} from '@angular/material/tree';
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
} from '@angular/forms';
import {ErrorStateMatcher} from '@angular/material/core';
import {MatDialog} from '@angular/material/dialog';
import {MatToolbar} from '@angular/material/toolbar';
import {MatButton, MatIconButton} from '@angular/material/button';
import {MatIcon} from '@angular/material/icon';
import {NgClass, CurrencyPipe} from '@angular/common';
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
import {MatError, MatFormField, MatSuffix} from '@angular/material/form-field';
import {MatInput} from '@angular/material/input';
import {MatProgressSpinner} from '@angular/material/progress-spinner';
import {MatSnackBar, MatSnackBarModule} from '@angular/material/snack-bar';
import {MatTooltip} from '@angular/material/tooltip';
import {firstValueFrom} from 'rxjs';

import {
  BankAccountRead,
  BudgetAssistantApiService,
  BudgetTreeCreate,
  BudgetTreeNodeRead,
  BudgetTreeNodeUpdate,
  BudgetTreeRead
} from '@daanvdn/budget-assistant-client';
import {injectQuery, injectQueryClient} from '@tanstack/angular-query-experimental';

import {AppService} from '../app.service';
import {BankAccountSelectionComponent} from '../bank-account-selection/bank-account-selection.component';
import {SaveErrorDialogComponent, SaveErrorDialogData} from './save-error-dialog/save-error-dialog.component';

// ---------------------------------------------------------------------------
// Flat node used by FlatTreeControl
// ---------------------------------------------------------------------------
export interface FlatBudgetNode {
  id: number;
  name: string;
  qualifiedName: string;
  amount: number;
  parentId: number | null;
  level: number;
  expandable: boolean;
}

// ---------------------------------------------------------------------------
// Error state matcher – shows errors immediately
// ---------------------------------------------------------------------------
class BudgetErrorStateMatcher implements ErrorStateMatcher {
  isErrorState(control: FormControl | null, _form: FormGroupDirective | NgForm | null): boolean {
    return !!(control && control.invalid && (control.dirty || control.touched));
  }
}

// Sentinel values for the "Totaal" row
const TOTAL_NODE_ID = -1;
const TOTAL_NODE_NAME = 'Totaal';

@Component({
  selector: 'app-budget',
  templateUrl: './budget.component.html',
  styleUrls: ['./budget.component.scss'],
  standalone: true,
  imports: [
    MatToolbar,
    BankAccountSelectionComponent,
    MatButton,
    MatIconButton,
    MatIcon,
    FormsModule,
    ReactiveFormsModule,
    MatTable,
    MatColumnDef,
    MatHeaderCellDef,
    MatHeaderCell,
    MatCellDef,
    MatCell,
    MatFormField,
    MatInput,
    MatError,
    MatSuffix,
    MatHeaderRowDef,
    MatHeaderRow,
    MatRowDef,
    MatRow,
    NgClass,
    MatProgressSpinner,
    MatSnackBarModule,
    MatTooltip,
    CurrencyPipe
  ]
})
export class BudgetComponent implements OnInit {

  // ── Dependency injection ──────────────────────────────────────────────
  private readonly destroyRef = inject(DestroyRef);
  private readonly appService = inject(AppService);
  private readonly apiService = inject(BudgetAssistantApiService);
  private readonly fb = inject(FormBuilder);
  private readonly dialog = inject(MatDialog);
  private readonly snackBar = inject(MatSnackBar);
  private readonly queryClient = injectQueryClient();

  // ── Constants ─────────────────────────────────────────────────────────
  readonly TOTAL_NODE_ID = TOTAL_NODE_ID;
  readonly displayedColumns: string[] = ['category', 'budget', 'yearlyBudget'];

  // ── Reactive state (signals) ──────────────────────────────────────────
  protected readonly selectedAccount = signal<BankAccountRead | undefined>(undefined);
  protected readonly dataLoaded = signal(false);
  protected readonly isTreeExpanded = signal(true);
  protected readonly isSaving = signal(false);
  protected readonly totalBudget = signal(0);

  // Sub-tree highlight state
  private readonly rowsToHighlight = signal<Set<number>>(new Set());
  protected readonly currentSubTreeHasError = signal(false);

  // ── Error state matcher ───────────────────────────────────────────────
  readonly matcher = new BudgetErrorStateMatcher();

  // ── Maps for tree / form management ───────────────────────────────────
  /** id → original nested BudgetTreeNodeRead node */
  private idToNodeMap = new Map<number, BudgetTreeNodeRead>();
  /** nested node → flat node (keeps same reference for CDK) */
  private nestedToFlatMap = new Map<BudgetTreeNodeRead, FlatBudgetNode>();
  /** id → FormControl */
  private idToControlMap = new Map<number, FormControl<number>>();
  /** FormControl → id */
  private controlToIdMap = new Map<FormControl<number>, number>();

  mainForm: FormGroup;

  // ── CDK Tree setup ────────────────────────────────────────────────────
  private treeFlattener = new MatTreeFlattener<BudgetTreeNodeRead, FlatBudgetNode>(
    this.transformNode.bind(this),
    node => node.level,
    node => node.expandable,
    node => node.children ?? []
  );

  treeControl = new FlatTreeControl<FlatBudgetNode>(
    node => node.level,
    node => node.expandable
  );

  dataSource = new MatTreeFlatDataSource<BudgetTreeNodeRead, FlatBudgetNode>(
    this.treeControl,
    this.treeFlattener
  );

  // ── TanStack Query for budget data ────────────────────────────────────
  budgetQuery = injectQuery(() => ({
    queryKey: ['budget', this.selectedAccount()?.accountNumber],
    queryFn: async () => {
      const account = this.selectedAccount();
      if (!account) throw new Error('No bank account selected');

      const budgetTreeCreate: BudgetTreeCreate = {bankAccountId: account.accountNumber};
      let first = firstValueFrom(
        this.apiService.budget.findOrCreateBudgetApiBudgetFindOrCreatePost(budgetTreeCreate)
      );
      return first;
    },
    enabled: !!this.selectedAccount(),
  }));

  // ── Computed helpers ──────────────────────────────────────────────────
  protected readonly isLoading = computed(() => this.budgetQuery.isPending() && !!this.selectedAccount());

  /** Track whether data has been initialised to avoid re-running setup. */
  private _lastBudgetKey: string | undefined;

  constructor() {
    this.mainForm = this.fb.group({});

    // Use effect to react to query data changes — this is allowed to write signals
    effect(() => {
      const data = this.budgetQuery.data();
      if (!data) return;

      const key = data.bankAccountId + '_' + data.rootId;
      if (key !== this._lastBudgetKey) {
        this._lastBudgetKey = key;
        this.onBudgetDataReady();
      }
    }, {allowSignalWrites: true});
  }

  // ── Lifecycle ─────────────────────────────────────────────────────────
  ngOnInit(): void {
    // React to bank-account changes from the global selector
    this.appService.selectedBankAccountObservable$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(account => {
        if (account) {
          this.selectedAccount.set(account);
        }
      });
  }

  /**
   * Called from the template when the budgetQuery data arrives (via effect-like
   * subscription on the query result). We set up the tree + forms here.
   */
  protected onBudgetDataReady(): void {
    const budgetTree: BudgetTreeRead | undefined = this.budgetQuery.data();
    if (!budgetTree?.root) return;

    this.resetState();
    const rootChildren = budgetTree.root.children ?? [];

    // Filter out dummy categories
    const filtered = rootChildren.filter(
      n => n.name !== 'NO CATEGORY' && n.name !== 'DUMMY CATEGORY'
    );

    // Collect ALL nodes (recursively) for form registration
    const allNodes: BudgetTreeNodeRead[] = [];
    for (const node of filtered) {
      this.collectAllNodes(node, allNodes);
    }

    // Register form controls for every node
    for (const node of allNodes) {
      this.registerFormControl(node);
    }

    // Build the data source; append a virtual total node
    const totalNode = this.buildTotalNode();
    this.dataSource.data = [...filtered, totalNode];

    this.recalcTotal();
    this.dataLoaded.set(true);
    this.treeControl.expandAll();
    this.isTreeExpanded.set(true);
  }

  // ── CDK Tree transformer ─────────────────────────────────────────────
  private transformNode(node: BudgetTreeNodeRead, level: number): FlatBudgetNode {
    const existing = this.nestedToFlatMap.get(node);
    if (existing && existing.qualifiedName === (node.qualifiedName ?? '')) {
      // Reuse existing flat node to keep CDK references stable
      existing.amount = node.amount;
      existing.level = level;
      return existing;
    }

    const flat: FlatBudgetNode = {
      id: node.id,
      name: node.name ?? '',
      qualifiedName: node.qualifiedName ?? '',
      amount: node.amount,
      parentId: node.parentId ?? null,
      level,
      expandable: !!(node.children && node.children.length > 0)
    };

    this.idToNodeMap.set(node.id, node);
    this.nestedToFlatMap.set(node, flat);
    return flat;
  }

  hasChild = (_: number, node: FlatBudgetNode) => node.expandable;

  // ── Form registration ─────────────────────────────────────────────────
  private registerFormControl(node: BudgetTreeNodeRead): void {
    const control = new FormControl<number>(node.amount, {
      nonNullable: true,
      validators: [this.negativeValidator(), this.descendantSumValidator(node.id)]
    });

    control.valueChanges
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(value => {
        if (value === undefined || value === null) return;

        // Sync the amount back to the nested node
        const nested = this.idToNodeMap.get(node.id);
        if (nested) nested.amount = value;

        // Re-validate parent controls (they depend on children values)
        this.revalidateAncestors(node.id);
        this.recalcTotal();

        // Determine subtree highlight
        const flat = this.nestedToFlatMap.get(nested!);
        if (flat && flat.name !== TOTAL_NODE_NAME) {
          this.determineSubTree(flat);
          // Auto-save when valid
          if (!this.currentSubTreeHasError()) {
            this.saveSingleNode(flat);
          }
        }
      });

    this.idToControlMap.set(node.id, control);
    this.controlToIdMap.set(control, node.id);
    this.mainForm.addControl(node.id.toString(), control);
  }

  // ── Validators ────────────────────────────────────────────────────────
  private negativeValidator(): ValidatorFn {
    return (control: AbstractControl) => {
      return control.value < 0 ? {negativeNumber: {value: control.value}} : null;
    };
  }

  private descendantSumValidator(nodeId: number): ValidatorFn {
    return (control: AbstractControl) => {
      const node = this.idToNodeMap.get(nodeId);
      if (!node || control.value == null || control.value < 0) return null;

      const descendantSum = this.sumOfDescendants(node);
      return control.value < descendantSum
        ? {isLessThanItsDescendants: {value: control.value}}
        : null;
    };
  }

  private sumOfDescendants(node: BudgetTreeNodeRead): number {
    let sum = 0;
    const stack = [...(node.children ?? [])];
    while (stack.length > 0) {
      const child = stack.pop()!;
      const ctrl = this.idToControlMap.get(child.id);
      if (ctrl && ctrl.value > 0) sum += ctrl.value;
      if (child.children) stack.push(...child.children);
    }
    return sum;
  }

  /** Re-validate ancestor chain so parent constraints update immediately. */
  private revalidateAncestors(nodeId: number): void {
    let current = this.idToNodeMap.get(nodeId);
    while (current?.parentId != null) {
      const parentCtrl = this.idToControlMap.get(current.parentId);
      if (parentCtrl) {
        parentCtrl.updateValueAndValidity({onlySelf: true, emitEvent: false});
      }
      current = this.idToNodeMap.get(current.parentId);
    }
  }

  // ── Sub-tree highlight ────────────────────────────────────────────────
  determineSubTree(flatNode: FlatBudgetNode): void {
    const ids = new Set<number>();
    const node = this.idToNodeMap.get(flatNode.id);
    if (!node) return;

    // Find the "local root" — go up 1 level if there's a parent
    const localRoot = node.parentId != null
      ? this.idToNodeMap.get(node.parentId) ?? node
      : node;

    // Add local root + all descendants
    ids.add(localRoot.id);
    this.collectDescendantIds(localRoot, ids);

    this.rowsToHighlight.set(ids);
    this.currentSubTreeHasError.set(this.anyControlInvalid(ids));
  }

  private collectDescendantIds(node: BudgetTreeNodeRead, ids: Set<number>): void {
    for (const child of node.children ?? []) {
      ids.add(child.id);
      this.collectDescendantIds(child, ids);
    }
  }

  private anyControlInvalid(ids: Set<number>): boolean {
    for (const id of ids) {
      const ctrl = this.mainForm.get(id.toString());
      if (ctrl?.invalid) return true;
    }
    return false;
  }

  // ── Row class helper ──────────────────────────────────────────────────
  getRowClass(node: FlatBudgetNode): string {
    if (node.name === TOTAL_NODE_NAME) return 'highlight-total-row';
    if (!this.rowsToHighlight().has(node.id)) return '';
    return this.currentSubTreeHasError() ? 'highlight-row-error' : 'highlight-row-no-error';
  }

  // ── Saving ────────────────────────────────────────────────────────────
  private saveSingleNode(flatNode: FlatBudgetNode): void {
    const ctrl = this.idToControlMap.get(flatNode.id);
    if (!ctrl || !ctrl.valid) return;

    const node = this.idToNodeMap.get(flatNode.id);
    if (!node || node.amount === ctrl.value) return; // no change

    node.amount = ctrl.value;
    const update: BudgetTreeNodeUpdate = {amount: ctrl.value};
    this.apiService.budget.updateBudgetEntryAmountApiBudgetEntryNodeIdPatch(node.id, update)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        error: (err) => {
          console.error('Failed to update budget entry:', err);
          this.snackBar.open('Fout bij opslaan', 'Sluiten', {duration: 3000});
        }
      });
  }

  saveAll(): void {
    // Validate all controls first
    this.mainForm.markAllAsTouched();
    Object.keys(this.mainForm.controls).forEach(key => {
      this.mainForm.get(key)?.updateValueAndValidity({onlySelf: false, emitEvent: false});
    });

    if (this.mainForm.invalid) {
      const invalidNodes: BudgetTreeNodeRead[] = [];
      for (const [id, ctrl] of this.idToControlMap) {
        if (ctrl.invalid) {
          const node = this.idToNodeMap.get(id);
          if (node) invalidNodes.push(node);
        }
      }
      const dialogData: SaveErrorDialogData = {
        message: 'Sommige wijzigingen kunnen niet worden opgeslagen! Corrigeer de inconsistente budgetbedragen voor onderstaande categorieën en probeer opnieuw:',
        nodes: invalidNodes
      };
      this.dialog.open(SaveErrorDialogComponent, {data: dialogData});
      return;
    }

    // Save all dirty nodes
    this.isSaving.set(true);
    const promises: Promise<any>[] = [];

    for (const [id, ctrl] of this.idToControlMap) {
      if (id === TOTAL_NODE_ID) continue;
      const node = this.idToNodeMap.get(id);
      if (!node) continue;

      if (node.amount !== ctrl.value) {
        node.amount = ctrl.value;
      }

      const update: BudgetTreeNodeUpdate = {amount: ctrl.value};
      promises.push(
        firstValueFrom(
          this.apiService.budget.updateBudgetEntryAmountApiBudgetEntryNodeIdPatch(node.id, update)
        )
      );
    }

    Promise.all(promises)
      .then(() => {
        this.snackBar.open('Budget opgeslagen', 'Sluiten', {duration: 2000});
        // Invalidate TanStack cache so a re-fetch picks up server state
        this.queryClient.invalidateQueries({queryKey: ['budget']});
      })
      .catch(err => {
        console.error('Error saving budget:', err);
        this.snackBar.open('Fout bij opslaan van budget', 'Sluiten', {duration: 3000});
      })
      .finally(() => this.isSaving.set(false));
  }

  // ── Expand / Collapse ─────────────────────────────────────────────────
  toggleTree(): void {
    if (this.isTreeExpanded()) {
      this.treeControl.collapseAll();
    } else {
      this.treeControl.expandAll();
    }
    this.isTreeExpanded.update(v => !v);
  }

  // ── Total budget calculation ──────────────────────────────────────────
  private recalcTotal(): void {
    let sum = 0;
    // Only sum root-level nodes (top-level categories)
    const roots = this.dataSource.data.filter(n => n.id !== TOTAL_NODE_ID);
    for (const root of roots) {
      const ctrl = this.idToControlMap.get(root.id);
      if (ctrl && ctrl.valid) {
        sum += ctrl.value ?? 0;
      }
    }
    this.totalBudget.set(sum);

    // Update the total node in the last position
    const data = this.dataSource.data;
    const totalIdx = data.findIndex(n => n.id === TOTAL_NODE_ID);
    if (totalIdx >= 0) {
      // Mutate amount in-place so the CDK flat node picks it up
      data[totalIdx] = {...data[totalIdx], amount: sum};
      // We do NOT rebuild `dataSource.data` — this preserves expand/collapse state
    }
  }

  // ── Helpers ───────────────────────────────────────────────────────────
  private buildTotalNode(): BudgetTreeNodeRead {
    return {
      id: TOTAL_NODE_ID,
      amount: 0,
      name: TOTAL_NODE_NAME,
      qualifiedName: TOTAL_NODE_NAME,
      children: []
    };
  }

  private collectAllNodes(node: BudgetTreeNodeRead, result: BudgetTreeNodeRead[]): void {
    result.push(node);
    for (const child of node.children ?? []) {
      this.collectAllNodes(child, result);
    }
  }

  private resetState(): void {
    this.dataLoaded.set(false);
    this.idToNodeMap.clear();
    this.nestedToFlatMap.clear();
    this.idToControlMap.clear();
    this.controlToIdMap.clear();
    this.mainForm = this.fb.group({});
    this.rowsToHighlight.set(new Set());
    this.currentSubTreeHasError.set(false);
  }

}
