import { AbstractControl, ControlValueAccessor, FormBuilder, NG_VALIDATORS, NG_VALUE_ACCESSOR, ValidationErrors, Validator, ValidatorFn, Validators, FormsModule, ReactiveFormsModule } from '@angular/forms';
import {
  CategoricalOperators, Comparator,
  Field, FieldType,
  LocalRuleMeta,
  MATCH_TYPES, MatchTypes,
  MultiMap, NumericalOperators, Operator,
  Option,
  QueryBuilderClassNames,
  QueryBuilderConfig,
  Rule,
  RuleSet,
  RuleUtils, StringOperators
} from './query-builder.interfaces';
import {
  ChangeDetectorRef, Component, ElementRef, forwardRef, HostBinding, Input, OnChanges, SimpleChanges, ViewChild
} from '@angular/core';
import {ErrorDialogService} from "../error-dialog/error-dialog.service";
import {AppService} from "../app.service";
import { MatExpansionPanel, MatExpansionPanelHeader } from "@angular/material/expansion";
import { NgClass, NgIf, NgFor, NgSwitch, NgSwitchCase } from '@angular/common';
import { MatButton, MatIconButton } from '@angular/material/button';
import { MatFormField, MatError } from '@angular/material/form-field';
import { MatSelect } from '@angular/material/select';
import { MatOption } from '@angular/material/core';
import { MatInput } from '@angular/material/input';
import { MatIcon } from '@angular/material/icon';
import { MatCheckbox } from '@angular/material/checkbox';
import {FieldTypeEnum, RuleMatchType, RuleOperator, ConditionEnum} from './query-builder.interfaces';


export class FieldsMetaData {

  type2fields = new MultiMap<string, Field>();
  field2Type = new Map<string, string>;


  fieldToOptions = new MultiMap<string, Option>();

  public registerField(field: Field): void {
    this.type2fields.set(field.type, field);
    this.field2Type.set(field.name as string, field.type);

    if (field.options) {
      for (const option of field.options) {
        this.fieldToOptions.set(field.name as string, option);
      }
    }

  }

  public getFieldTypes(): string[] {
    return this.type2fields.keys();
  }

  public getFieldType(field: string) {
    let type = this.field2Type.get(field);
    if (!type) {
      return null;
    }

    return type;
  }


}

export const CONTROL_VALUE_ACCESSOR: any = {
  provide: NG_VALUE_ACCESSOR,
  useExisting: forwardRef(() => QueryBuilderComponent),
  multi: true
};

export const VALIDATOR: any = {
  provide: NG_VALIDATORS,
  useExisting: forwardRef(() => QueryBuilderComponent),
  multi: true
};


@Component({
    selector: 'query-builder',
    templateUrl: './query-builder.component.html',
    styleUrls: ['./query-builder.component.scss'],
    providers: [CONTROL_VALUE_ACCESSOR, VALIDATOR],
    standalone: true,
    imports: [NgClass, NgIf, FormsModule, NgFor, MatButton, ReactiveFormsModule, MatFormField, MatSelect, MatOption, NgSwitch, NgSwitchCase, MatError, MatExpansionPanel, MatExpansionPanelHeader, MatInput, MatIconButton, MatIcon, MatCheckbox]
})
export class QueryBuilderComponent implements OnChanges, ControlValueAccessor, Validator {

  protected readonly MATCH_TYPES = MATCH_TYPES;
  protected readonly RuleUtils = RuleUtils;
  public typeToFieldMapWrapper = new FieldsMetaData();
  public fields: Field[];
  public filterFields: Field[];
  public fieldNames: string[];
  public panelOpenState: boolean = true;

  public defaultClassNames: QueryBuilderClassNames = {
    arrowIconButton: 'q-arrow-icon-button',
    arrowIcon: 'q-icon q-arrow-icon',
    removeIcon: 'q-icon q-remove-icon',
    addIcon: 'q-icon q-add-icon',
    button: 'q-button',
    buttonGroup: 'q-button-group',
    removeButton: 'q-remove-button',
    switchGroup: 'q-switch-group',
    switchLabel: 'q-switch-label',
    switchRadio: 'q-switch-radio',
    rightAlign: 'q-right-align',
    transition: 'q-transition',
    collapsed: 'q-collapsed',
    treeContainer: 'q-tree-container',
    tree: 'q-tree',
    row: 'q-row',
    connector: 'q-connector',
    rule: 'q-rule',
    ruleSet: 'q-ruleset',
    invalidRuleSet: 'q-invalid-ruleset',
    emptyWarning: 'q-empty-warning',
    fieldControl: 'q-field-control',
    fieldControlSize: 'q-control-size',
    operatorControl: 'q-operator-control',
    operatorControlSize: 'q-control-size',
    inputControl: 'q-input-control',
    inputControlSize: 'q-control-size'
  };
  @Input() disabled = false;
  @Input() data: RuleSet = new RuleSet('and', []);


  @HostBinding('attr.query-builder-condition') get condition() {
    return this.data?.condition;
  }

  // For ControlValueAccessor interface
  public onChangeCallback!: () => void;
  public onTouchedCallback!: () => any;

  @Input() allowRuleset = true;
  @Input() allowCollapse = false;
  @Input() emptyMessage = 'A ruleset cannot be empty. Please add a rule or remove it all together.';
  @Input() classNames: QueryBuilderClassNames = {};
  @Input() operatorMap: { [key: string]: string[] } = {};
  @Input() parentValue?: RuleSet;
  @Input() config: QueryBuilderConfig = {fields: {}};


  @Input() parentChangeCallback!: () => void;
  @Input() parentTouchedCallback!: () => void;
  @Input() persistValueOnFieldChange = false;

  @ViewChild('treeContainer', {static: true}) treeContainer!: ElementRef;


  constructor(private changeDetectorRef: ChangeDetectorRef, private formBuilder: FormBuilder,
              private errorDialogService: ErrorDialogService, private appService: AppService
  ) {
    this.fields = [];
    this.fieldNames = [];
    this.filterFields = [];

  }

  // ----------OnInit Implementation----------

  // ----------OnChanges Implementation----------


  compareMatSelectItems(o1: any, o2: any): boolean {

    return new Comparator().equals(o1, o2);

  }

  recurivelySetRuleFormField(ruleSet: RuleSet): void {
    if (ruleSet.rules) {
      for (let rule of ruleSet.rules) {
        if (rule.rules) {
          this.recurivelySetRuleFormField(rule as RuleSet);
        } else {
          this.handleFormForRule(rule as Rule);
        }
      }
    }

    this.changeInput();

  }


  ngOnChanges(changes: SimpleChanges) {
    if (changes['data'] && changes['data'].currentValue !== changes['data'].previousValue) {
      let currentRuleSet: RuleSet = changes['data'].currentValue as RuleSet;
      this.recurivelySetRuleFormField(currentRuleSet);

    }
    const config = this.config;
    const type = typeof config;
    if (type === 'object') {

      this.fields = Object.keys(config.fields).map((value) => {
        const field = config.fields[value];
        field.value = field.value || value;
        if (field.type && field.type !== 'category') {
          this.typeToFieldMapWrapper.registerField(field);
        }
        return field;
      });

    } else {
      throw new Error(`Expected 'config' must be a valid object, got ${type} instead.`);
    }

  }

  removeStringValueFromStringField(index: number, rule: Rule): void {

    if (this.disabled) {
      return;
    }
    //remove the item in rule.value at the index position
    rule.value?.splice(index, 1);
    this.handleDataChange();
    this.handleTouched();
  }

  submitHandler(e: any) {
    e.preventDefault();
  }

  addStringValue(rule: Rule, expansionPanel: MatExpansionPanel): void {
    let formcontrol = rule.ruleForm?.get('fieldValueGroup')?.get('inputTextForStringField');
    if (!formcontrol) {
      throw new Error("Form control not found!");
    }
    let input = formcontrol?.value;
    if (!input || input === '') {


      this.changeDetectorRef.detectChanges(); // Add this line
      // Wrap the expansionPanel.open() call inside a setTimeout function
      setTimeout(() => {
        expansionPanel.open();
      }, 0);
      return;
    }
    if (rule.value === undefined) {
      rule.value = [];
    }


    // Check if the value is not already in the array
    if (rule.value.indexOf(input) === -1) {
      // Directly push the value to the rule.value array
      rule.value.push(input);
      // formcontrol.reset();
      this.handleTouched();
      this.handleDataChange();
      this.changeDetectorRef.detectChanges(); // Add this line
      // Wrap the expansionPanel.open() call inside a setTimeout function
      setTimeout(() => {
        expansionPanel.open();
      }, 0);
    }
    formcontrol.reset();

    this.changeDetectorRef.detectChanges(); // Add this line
    // Wrap the expansionPanel.open() call inside a setTimeout function
    setTimeout(() => {
      expansionPanel.open();
    }, 0);

  }

  // ----------Validator Implementation----------

  validate(control: AbstractControl): ValidationErrors | null {
    const errors: { [key: string]: any } = {};
    const ruleErrorStore = [] as any;
    let hasErrors = false;

    if (!this.config.allowEmptyRulesets && this.checkEmptyRuleInRuleset(this.data)) {
      errors['empty'] = 'Empty rulesets are not allowed.';
      hasErrors = true;
    }


    if (ruleErrorStore.length) {
      errors['rules'] = ruleErrorStore;
      hasErrors = true;
    }
    return hasErrors ? errors : null;
  }

  // ----------ControlValueAccessor Implementation----------

  @Input()
  get value(): RuleSet {
    return this.data;
  }

  set value(value: RuleSet) {
    // When component is initialized without a formControl, null is passed to value
    this.data = value || new RuleSet('and', []);
    this.recurivelySetRuleFormField(this.data);
    this.handleDataChange();
  }

  writeValue(obj: any): void {
    this.value = obj;
  }

  registerOnChange(fn: any): void {
    this.onChangeCallback = () => fn(this.data);
  }

  registerOnTouched(fn: any): void {
    this.onTouchedCallback = () => fn(this.data);
  }

  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
    this.changeDetectorRef.detectChanges();
  }

  // ----------END----------

  getDisabledState = (): boolean => {
    return this.disabled;
  }


  getFieldsForSelectedType(rule: Rule): Field[] {
    if (rule.fieldType) {
      let fields = this.typeToFieldMapWrapper.type2fields.get(rule.fieldType) as Field[];
      return fields;
    }
    return [];
  }

  getOptionsForField(rule: Rule): Option[] {

    if (!rule.field) {
      return [];
    }
    if (RuleUtils.fieldIsArray(rule) && (rule.field as any).length > 1) {
      throw new Error('Expected field to not be an array!');

    }


    //get random element from set and get options

    let options = (rule.field as any).options;
    if (!options) {
      return [];
    }
    return options as Option[];

  }


  getOperatorsForSelectedType(rule: Rule): Operator[] {
    const fieldType = rule.fieldType;
    if (!fieldType) {
      return [];
    }
    switch (fieldType) {
      case "string":
        return StringOperators.ALL;
      case "number":
        return NumericalOperators.ALL;
      case "categorical":
        return CategoricalOperators.ALL;
      default:
        throw new Error(`Unexpected field type: ${fieldType}`);

    }


  }


  getClassNames(...args: string[]): any | string[] {
    const clsLookup = this.classNames ? this.classNames : this.defaultClassNames as any;
    const defaultClassNames = this.defaultClassNames as any;
    const classNames = args.map((id: any) => clsLookup[id] || defaultClassNames[id]).filter((c: any) => !!c);
    return classNames.length ? classNames.join(' ') : [];
  }


  public oneControlIsNotEmptyValidator(controlNames: string[]): ValidatorFn {
    return (control: AbstractControl): { [key: string]: any } | null => {
      let controls = new Array<AbstractControl>();
      for (const controlName of controlNames) {
        controls.push(control.get(controlName) as AbstractControl);
      }

      //logic to count how many controls are empty
      let emptyCount = 0;
      for (const control of controls) {
        if (control.value == null || control.value === '') {
          emptyCount++;
        }
      }
      // If all controls are empty, return an error
      if (emptyCount === controls.length) {
        // return {oneControlRequired: true};
        return {oneControlRequired: true};
      }

      // If at least one control is non-empty, no error
      return null;
    };
  }

  currentRuleSetIsInvalid(ruleSet: RuleSet): boolean {
    if (ruleSet.rules) {
      return ruleSet.rules.some((item: RuleSet | any) => {
        if (item.rules) {
          return this.currentRuleSetIsInvalid(item);
        } else {
          return this.currentRuleIsInvalid(item);
        }
      });
    }
    return false;
  }

  currentRuleIsInvalid(rule: Rule): boolean {
    return !RuleUtils.isValid(rule);
  }

  addRule(parent?: RuleSet): void {
    if (this.disabled) {
      return;
    }

    parent = parent || this.data;
    if (parent.rules && parent.rules.length > 0) {
      //get last item of rules
      let lastItem = parent.rules[parent.rules.length - 1];
      if (!(RuleUtils.isRuleSetObject(lastItem)) && this.currentRuleIsInvalid(lastItem as Rule)) {
        this.errorDialogService.openErrorDialog("Error", "Please fill out the current rule before adding a new one!");
        return;
      }


    }


    let rule: Rule = new Rule([], 'string', undefined, [], undefined, undefined, undefined);
    this.handleFormForRule(rule);

    parent.rules = parent.rules.concat([rule]);

    this.handleTouched();
    this.handleDataChange();
  }

  handleFormForRule(rule: Rule) {
    if (rule.ruleForm) {
      //the form is already created; nothing to do
      return;
    }
    rule.ruleForm = this.formBuilder.group({
      fieldType: ['string', Validators.required],
      fieldMatchType: ['', Validators.required],
      fieldGroup: this.formBuilder.group({
        fieldSingle: ['', Validators.required], fieldMultiple: ['', Validators.required],
      }, {validators: this.oneControlIsNotEmptyValidator(['fieldSingle', 'fieldMultiple'])}),
      operator: ['', Validators.required],
      valueMatchType: ['', Validators.required],
      fieldValueGroup: this.formBuilder.group({
        inputTextForStringField: ['', /*Validators.required*/], // fieldValueNumber: ['', /*Validators.required*/],
        // fieldValueDate: ['', /*Validators.required*/],
        // fieldValueTime: ['', /*Validators.required*/],
        fieldValueCategorical: ['', /*Validators.required*/], // fieldValueBoolean: ['', /*Validators.required*/],
      })

    });

    if (rule.fieldType) {
      let fieldType: AbstractControl = rule.ruleForm.get('fieldType') as AbstractControl;
      fieldType.setValue(rule.fieldType);
    }

    rule.ruleForm.get('fieldType')?.valueChanges.subscribe((value) => {
      this.changeFieldType(value, rule);
    });

    if (rule.fieldMatchType) {
      let fieldMatchType = rule.ruleForm.get('fieldMatchType') as AbstractControl;
      fieldMatchType.setValue(rule.fieldMatchType);
    }
    rule.ruleForm.get('fieldMatchType')?.valueChanges.subscribe((value) => {
      this.changeFieldMatchType(value, rule);

    });

    if (rule.field) {
      if (RuleUtils.allowMultipleFields(rule)) {

        rule.ruleForm.get("fieldGroup")?.get('fieldMultiple')?.setValue(rule.field);
      } else {

        rule.ruleForm.get("fieldGroup")?.get('fieldSingle')?.setValue(rule.field);
      }
    }

    rule.ruleForm.get("fieldGroup")?.get('fieldMultiple')?.valueChanges.subscribe((value) => {
      this.changeFieldArray(value, rule);
    });
    rule.ruleForm.get("fieldGroup")?.get('fieldSingle')?.valueChanges.subscribe((value) => {
      this.changeField(value, rule);
    });

    if (rule.operator) {
      rule.ruleForm.get('operator')?.setValue(rule.operator);
    }

    rule.ruleForm.get('operator')?.valueChanges.subscribe((value) => {
      this.changeOperator(value, rule);

    });

    if (rule.valueMatchType) {
      rule.ruleForm.get('valueMatchType')?.setValue(rule.valueMatchType);
    }

    rule.ruleForm.get('valueMatchType')?.valueChanges.subscribe((value) => {
      this.changeValueMatchType(value, rule);

    });
    rule.ruleForm.get('fieldValueGroup')?.get('inputTextForStringField')?.valueChanges.subscribe((value) => {

    });

    /*rule.ruleForm.get('fieldValueGroup')?.get('fieldValueNumber')?.valueChanges.subscribe((value) => {
      rule.value = value;
      this.changeInput();
    });
    rule.ruleForm.get('fieldValueGroup')?.get('fieldValueDate')?.valueChanges.subscribe((value) => {
      rule.value = value;
      this.changeInput();
    });
    rule.ruleForm.get('fieldValueGroup')?.get('fieldValueTime')?.valueChanges.subscribe((value) => {
      rule.value = value;
      this.changeInput();
    });*/
    rule.ruleForm.get('fieldValueGroup')?.get('fieldValueCategorical')?.valueChanges.subscribe((value) => {
      rule.value = value;
      this.changeInput();
    });

    /*rule.ruleForm.get('fieldValueGroup')?.get('fieldValueBoolean')?.valueChanges.subscribe((value) => {
      rule.value = value;
      this.changeInput();
    });*/
  }

  removeRule(rule: Rule, parent?: RuleSet): void {
    if (this.disabled) {
      return;
    }

    parent = parent || this.data;

    parent.rules = parent.rules.filter((r) => r !== rule);


    this.handleTouched();
    this.handleDataChange();
  }

  addRuleSet(parent?: RuleSet): void {
    if (this.disabled) {
      return;
    }

    parent = parent || this.data;
    //set lastItem to last item of rules or undefined if RuleSet.rules is undefined
    let lastItem = parent.rules=== undefined? undefined : parent.rules[parent.rules.length - 1];

    // let lastItem = parent.rules[parent.rules.length - 1];
    if ( lastItem && (RuleUtils.isRuleSetObject(lastItem)) && this.currentRuleSetIsInvalid(lastItem as RuleSet)) {
      this.errorDialogService.openErrorDialog("Error", "Please fill out the current rule before adding a new one!");
      return;
    } else if ( lastItem &&!(RuleUtils.isRuleSetObject(lastItem)) && this.currentRuleIsInvalid(lastItem as Rule)) {
      this.errorDialogService.openErrorDialog("Error", "Please fill out the current rule before adding a new one!");
      return;
    }


    let ruleSet: RuleSet = new RuleSet('and', []);
    parent.rules = parent.rules.concat([ruleSet]);


    this.handleTouched();
    this.handleDataChange();
  }

  removeRuleSet(ruleset?: RuleSet, parent?: RuleSet): void {
    if (this.disabled) {
      return;
    }

    ruleset = ruleset || this.data;
    parent = parent || this.parentValue;
    if (parent) {
      parent.rules = parent.rules.filter((r) => r !== ruleset);
    }

    this.handleTouched();
    this.handleDataChange();
  }

  transitionEnd(e: Event): void {
    this.treeContainer.nativeElement.style.maxHeight = null;
  }

  toggleCollapse(): void {
    this.computedTreeContainerHeight();
    setTimeout(() => {
      this.data.collapsed = !this.data.collapsed;
    }, 100);
  }

  computedTreeContainerHeight(): void {
    const nativeElement: HTMLElement = this.treeContainer.nativeElement;
    if (nativeElement && nativeElement.firstElementChild) {
      nativeElement.style.maxHeight = (nativeElement.firstElementChild.clientHeight + 8) + 'px';
    }
  }

  changeCondition(value: string): void {
    if (this.disabled) {
      return;
    }
    //check that value satisfies ConditionEnum
    if (value.toLowerCase() !== 'and' && value.toLowerCase() !== 'or') {
      throw new Error('Invalid condition value');
    }
    this.data.condition = value.toUpperCase() as  ConditionEnum;
    this.handleTouched();
    this.handleDataChange();
    this.changeDetectorRef.detectChanges();
  }

  changeOperator(value: Operator, rule: Rule): void {
    if (this.disabled) {
      return;
    }
    rule.operator = value as any;


    this.handleTouched();
    this.handleDataChange();
    this.changeDetectorRef.detectChanges(); // Add this line
  }


  changeFieldMatchType(fieldMatchType: RuleMatchType, rule: Rule): void {
    if (this.disabled) {
      return;
    }

    rule.fieldMatchType = fieldMatchType;
    this.handleTouched();
    this.handleDataChange();
    this.changeDetectorRef.detectChanges(); // Add this line
  }

  changeValueMatchType(valueMatchType: RuleMatchType, rule: Rule): void {
    if (this.disabled) {
      return;
    }

    rule.valueMatchType = valueMatchType;
    this.handleTouched();
    this.handleDataChange();
    this.changeDetectorRef.detectChanges(); // Add this line
  }


  changeInput(): void {
    if (this.disabled) {
      return;
    }

    this.handleTouched();
    this.handleDataChange();
    this.changeDetectorRef.detectChanges(); // Add this line
  }

  changeField(field: Field, rule: Rule): void {
    if (this.disabled) {
      return;
    }
    if (!field || !rule) {
      return;
    }


    // delete rule.value;
    rule.field = [field.name];
    if (field.operators?.[0] !== undefined){

      rule.operator = field.operators?.[0].asOperator() as RuleOperator;
    }

    this.handleTouched();
    this.handleDataChange();
    this.changeDetectorRef.detectChanges(); // Add this line
  }

  changeFieldArray(field: Field[], rule: Rule): void {
    if (this.disabled) {
      return;
    }


    rule.value = [];
    if (!rule.field) {
      rule.field = [];
    } else {
      if (!RuleUtils.fieldIsArray(rule)) {
        throw new Error('Expected field to be an array!');
      }
    }
    //check if field is already in rule array
    let fieldArray: Field[] = rule.field as any;
    for (const fieldItem of field) {
      if (fieldArray.indexOf(fieldItem) === -1) {
        fieldArray.push(fieldItem);
      }
    }
    rule.field = fieldArray.map((f) => f.name);

    let operator = field[0]?.operators?.[0];
    if (operator){

      rule.operator = operator as any;
    } else {
        rule.operator = StringOperators.CONTAINS as any;
    }


    this.handleTouched();
    this.handleDataChange();
    this.changeDetectorRef.detectChanges(); // Add this line
  }

  changeFieldType(fieldType: FieldType, rule: Rule): void {
    if (this.disabled) {
      return;
    }
    if(fieldType === null){
      return;
    }


    rule.fieldType = fieldType as FieldTypeEnum;
    rule.field = [];
    rule.fieldMatchType = MatchTypes.ANY_OF.value;
    // delete rule.value;
    rule.valueMatchType = MatchTypes.ANY_OF.value;
    rule.operator = StringOperators.CONTAINS as any;


    this.handleTouched();
    this.handleDataChange();
    this.changeDetectorRef.detectChanges(); // Add this line
  }


  getQueryItemClassName(local: LocalRuleMeta): string {
    let cls = this.getClassNames('row', 'connector', 'transition');
    cls += ' ' + this.getClassNames(local.ruleset ? 'ruleSet' : 'rule');
    if (local.invalid) {
      cls += ' ' + this.getClassNames('invalidRuleSet');
    }
    return cls as string;
  }

  private checkEmptyRuleInRuleset(ruleset: RuleSet): boolean {
    if (!ruleset || !ruleset.rules || ruleset.rules.length === 0) {
      return true;
    } else {
      return ruleset.rules.some((item: RuleSet | any) => {
        if (item.rules) {
          return this.checkEmptyRuleInRuleset(item);
        } else {
          return false;
        }
      });
    }
  }

  private handleDataChange(): void {
    this.changeDetectorRef.markForCheck();
    if (this.onChangeCallback) {
      this.onChangeCallback();
    }
    if (this.parentChangeCallback) {
      this.parentChangeCallback();
    }
  }

  private handleTouched(): void {
    if (this.onTouchedCallback) {
      this.onTouchedCallback();
    }
    if (this.parentTouchedCallback) {
      this.parentTouchedCallback();
    }
  }

  getFieldTypes(): string[] {
    return this.typeToFieldMapWrapper.getFieldTypes();


  }




  showEmptyFieldNameError(rule: Rule): boolean {
    let fieldGroup = rule.ruleForm?.get("fieldGroup");
    if (RuleUtils.allowMultipleFields(rule)) {
      let errors = fieldGroup?.get('fieldMultiple')?.errors;
      if (errors && errors['required']) {
        return true;
      }
    } else {
      let errors = fieldGroup?.get('fieldSingle')?.errors;
      if (errors && errors['required']) {
        return true;
      }
    }
    return false;


  }

  showFieldMatchTypeError(rule: Rule) {
    let fieldMatchType = rule.ruleForm?.get("fieldMatchType");
    if (fieldMatchType && fieldMatchType.errors) {
      if (fieldMatchType.errors['required']) {
        return true;
      }

    }

    return false;
  }

  showOperatorError(rule: Rule) {
    let operator = rule.ruleForm?.get("operator");
    if (operator && operator.errors) {
      if (operator.errors['required']) {
        return true;
      }

    }

    return false;
  }

  showValueMatchTypeError(rule: Rule) {
    let valueMatchType = rule.ruleForm?.get("valueMatchType");
    if (valueMatchType && valueMatchType.errors) {
      if (valueMatchType.errors['required']) {
        return true;
      }

    }

    return false;
  }

  fieldValueIsEmpty(rule: Rule) {
    if (!rule.value) {
      return true;
    }
    if (Array.isArray(rule.value) && rule.value.length === 0) {
      return true;
    }

    return false;
  }


  requireExpansionPanelOpen(rule: Rule) {
    let value = rule.value;
    if (!value){

      return false;

    }

    if (Array.isArray(value) && value.length === 0) {
      return false;
    }
    return true;


  }
}
