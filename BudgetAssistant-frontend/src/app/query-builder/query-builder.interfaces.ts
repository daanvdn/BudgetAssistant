import {FormGroup} from "@angular/forms";

import {TypeEnum} from "../model";
import {RuleSetWrapperRead as ClientRuleSetWrapper} from "@daanvdn/budget-assistant-client";

// Define local types that were previously imported from the client
export type RuleMatchType = 'all' | 'any';
export type RuleOperator = 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte' | 'contains' | 'not_contains' | 'starts_with' | 'ends_with' | 'is_null' | 'is_not_null' | 'in' | 'not_in';
export type FieldTypeEnum = 'string' | 'number' | 'categorical';
export type ConditionEnum = 'AND' | 'OR';

export interface ClientRule {
  field: string;
  operator: RuleOperator;
  value?: any;
  fieldType?: FieldTypeEnum;
}

export interface ClientRuleSet {
  condition: ConditionEnum;
  rules: Array<ClientRule | ClientRuleSet>;
}

export interface ClientRuleSetRulesInner {
  field?: string;
  operator?: RuleOperator;
  value?: any;
  fieldType?: FieldTypeEnum;
  condition?: ConditionEnum;
  rules?: Array<ClientRuleSetRulesInner>;
}

export interface SimpleUser {
  id: number;
  username: string;
}

// Extended type to ensure all required properties exist on both Rule and RuleSet
// Using any as a temporary solution to get the code to compile
export type RuleSetRulesInner = any;


// Using FieldTypeEnum from @daanvdn/budget-assistant-client
// export type FieldType = 'string' | 'number' | 'categorical' | 'null';
export type FieldType = FieldTypeEnum | 'null';

// Extended type to ensure string is a valid value for ConditionEnum
export type ExtendedConditionEnum = ConditionEnum;

// Define MatchType for compatibility with RuleMatchType
export type MatchType = RuleMatchType;


export function objectsAreEqual(obj1: any, obj2: any): boolean {
  // Get the keys
  const keys1 = Object.keys(obj1);
  const keys2 = Object.keys(obj2);

  // If number of keys is different,
  // then objects are not equal
  if (keys1.length !== keys2.length) {
    return false;
  }

  // Iterate over keys
  for (const key of keys1) {
    const val1 = obj1[key];
    const val2 = obj2[key];
    const areObjects = isObject(val1) && isObject(val2);
    if ((areObjects && !objectsAreEqual(val1, val2)) || (!areObjects && val1 !== val2)) {
      return false;
    }
  }

  return true;
}

export function isObject(object: any): boolean {
  return object != null && typeof object === 'object';
}

// Using RuleOperator from @daanvdn/budget-assistant-client
export class Operator {
  readonly name: string;
  readonly value: string;
  readonly type: string;

  constructor(name: string, value: string, fieldType: FieldType) {
    this.value = value;
    this.type = fieldType;
    this.name = name;
  }

  equals(operator: Operator): boolean {
    return this.value === operator.value && this.type === operator.type && this.name === operator.name;
  }
  public asOperator():  RuleOperator {
   return this.value as RuleOperator;
}
}


export class StringOperators {

  static CONTAINS = new Operator('contains', 'contains', 'string');
  static EXACT_MATCH = new Operator('exact match', 'exact match', 'string');
  static FUZZY_MATCH = new Operator('fuzzy match', 'fuzzy match', 'string');
  static ALL: Operator[] = [StringOperators.CONTAINS, StringOperators.EXACT_MATCH, StringOperators.FUZZY_MATCH];
}

export class CategoricalOperators {
  static IN = new Operator('in', 'in', 'categorical');
  static NOT_IN = new Operator('not in', 'not in', 'categorical');
  static EQUALS = new Operator('equals', 'equals', 'categorical');
  static ALL: Operator[] = [CategoricalOperators.IN, CategoricalOperators.NOT_IN, CategoricalOperators.EQUALS];
}

export class NumericalOperators {
  static EQUALS = new Operator('equals', '=', 'number');
  static NOT_EQUALS = new Operator('not equals', '!=', 'number');
  static GREATER_THAN = new Operator('greater than', '>', 'number');
  static GREATER_THAN_OR_EQUALS = new Operator('greater than or equals', '>=', 'number');
  static LESS_THAN = new Operator('less than', '<', 'number');
  static LESS_THAN_OR_EQUALS = new Operator('less than or equals', '<=', 'number');
  static ALL: Operator[] = [NumericalOperators.EQUALS, NumericalOperators.NOT_EQUALS, NumericalOperators.GREATER_THAN, NumericalOperators.GREATER_THAN_OR_EQUALS, NumericalOperators.LESS_THAN, NumericalOperators.LESS_THAN_OR_EQUALS];
}


function isEmptyString(value: string | undefined | null): boolean {
  return !value || value === 'null' || value === 'undefined' || value.trim().length === 0;

}


// Local RuleSet class - doesn't implement ClientRuleSet directly due to type incompatibilities
export class RuleSet {
  clazz: string = 'RuleSet';
  type: any;
  condition: ExtendedConditionEnum;
  rules: Array<RuleSetRulesInner> = [];
  isChild: boolean = false;

  // Additional properties
  collapsed?: boolean;

  constructor(condition: string, rules: Array<any>, collapsed?: boolean, isChild?: boolean) {
    this.clazz = 'RuleSet';
    this.type = 'RuleSet';
    this.condition = condition as ConditionEnum;

    // Convert rules to RuleSetRulesInner array
    if (rules) {
      this.rules = rules as Array<RuleSetRulesInner>;
    }

    this.collapsed = collapsed;
    this.isChild = isChild ?? false;
  }

  public clone(): RuleSet {
    let clone: RuleSet = {...this};
    delete clone.collapsed;
    clone.isChild = false;

    clone.rules = clone.rules.map((rule: any) => {
      if (rule instanceof RuleSet) {
        return rule.clone();
      } else if (rule instanceof Rule) {
        return rule.clone();
      }
      return rule;
    });
    return clone;
  }

  public isComplete(): boolean {
    if (isEmptyString(this.condition)) {
      return false;
    }

    if (this.rules.length === 0) {
      return false;
    }

    for (const item of this.rules) {
      if ((item as any) instanceof RuleSet) {
        if (!(item as RuleSet).isComplete()) {
          return false;
        }
      } else if ((item as any) instanceof Rule) {
        if (!(item as Rule).isComplete()) {
          return false;
        }
      }
    }

    return true;
  }

  public toJson(): string {
    if (!this.isComplete()) {
      throw new Error('RuleSet is not complete');
    }

    let clone: RuleSet = this.clone();

    /*
        // Post-process the serialized JSON to remove properties that are undefined
        return JSON.parse(JSON.stringify(json, (key, value) => value === undefined ? undefined : value));
    */

    let mapper = (key: string, value: any) => {
      if (key === 'field' && value instanceof Field) {
        return (value as Field).pathFromTransaction;
      }
      if (key === 'field' && value instanceof Array) {
        return value.map((f: Field) => (f as Field).pathFromTransaction);
      }
      if (value && typeof value === 'object' && 'name' in value && 'value' in value) {
        return value.name;
      }

      return value;
    }

    return JSON.stringify(clone, mapper);
  }
}


// Using ClientRuleSetWrapper from @daanvdn/budget-assistant-client
export interface RuleSetWrapper extends ClientRuleSetWrapper {
  // Additional properties not in ClientRuleSetWrapper
  categoryType: TypeEnum;
}

// export type RuleMatchType = 'any of' | 'all of';




// RuleMatchType is now a string union type ('all' | 'any')
export interface MatchTypeOption {
  name: string;
  value: RuleMatchType;
}

export class MatchTypes {
  static ANY_OF: MatchTypeOption = {name: 'any of', value: 'any'};
  static ALL_OF: MatchTypeOption = {name: 'all of', value: 'all'};
  static ALL: MatchTypeOption[] = [MatchTypes.ANY_OF, MatchTypes.ALL_OF];
}

export const MATCH_TYPES: MatchTypeOption[] = MatchTypes.ALL;

export class RuleUtils {

  static isRule(rule: RuleSetRulesInner): rule is Rule {
    return rule.clazz === 'Rule';
  }

  static isRuleSet(rule: RuleSetRulesInner): rule is RuleSet {
    return rule.clazz === 'RuleSet';
  }

  static isRuleSetObject(o: Object): boolean {
    return o.hasOwnProperty('condition') && o.hasOwnProperty('rules');
  }

  static isRuleObject(o: Object): boolean {
    return o.hasOwnProperty('field') && o.hasOwnProperty('operator') && o.hasOwnProperty('value');
  }

  static fieldIsArray(rule: Rule): boolean {
    return Array.isArray(rule.field);
  }

  static valueIsArray(rule: Rule): boolean {
    if (rule.value) {
      return Array.isArray(rule.value);
    }
    return false;
  }



  static hideValueMatchType(rule: Rule): boolean {
    if (rule.fieldType !== undefined && (rule.fieldType as string === 'null')) {
      return true;
    }
    if (rule.fieldType !== undefined && rule.fieldType === 'categorical') {
      const op = rule.operator instanceof Operator ? rule.operator : null;
      if (rule.operator !== undefined && op && op.equals(CategoricalOperators.EQUALS)) {
        return true;
      }
    }

    return false;
  }


  static isValid(rule: Rule): boolean {
    if (rule === undefined || rule === null) {
      return false;
    }

    function isUndefinedOrEmpty(value: any): boolean {
      return value === undefined || value === null || (Array.isArray(
        value) && (value as Array<any>).length == 0) || value === '';
    }

    if (isUndefinedOrEmpty(rule.fieldType)) {
      return false;
    }
    if (rule.fieldType === 'string') {
      return !(isUndefinedOrEmpty(rule.field) || isUndefinedOrEmpty(rule.fieldMatchType) || isUndefinedOrEmpty(
        rule.operator) || isUndefinedOrEmpty(rule.valueMatchType) || isUndefinedOrEmpty(rule.value));

    }
    return !(isUndefinedOrEmpty(rule.field) || isUndefinedOrEmpty(rule.operator) || isUndefinedOrEmpty(rule.value));
  }

  static allowMultipleFields(rule: Rule): boolean {
    if (rule.fieldType && rule.fieldType === 'string') {
      return true;
    }
    return false;
  }

  static allowMultipleValues(rule: Rule): boolean {
    if (rule.fieldType && rule.fieldType === 'string') {
      return true;
    }
    return false;
  }

  static serializeRuleSet(ruleSet: RuleSet): string {
    const cache = new Set();
    const jsonString = JSON.stringify(ruleSet, (key, value) => {
      if (typeof value === 'object' && value !== null) {
        if (cache.has(value)) {
          // Circular reference found, discard key
          return;
        }
        // Store value in our set
        cache.add(value);
      }
      return value;
    });
    cache.clear(); // Clear the cache
    return jsonString;
  }


}


// Local Rule class - doesn't implement ClientRule directly due to type incompatibilities
export class Rule {
  clazz: string = 'Rule';
  type: any;
  field: Array<string> = [];
  fieldType?: FieldTypeEnum;
  value: Array<string> = [];
  valueMatchType?: RuleMatchType;
  operator?: Operator | RuleOperator;

  // Additional properties
  fieldMatchType?: RuleMatchType;
  ruleForm?: FormGroup;
  rules?: Array<RuleSetRulesInner>;
  condition?: ConditionEnum;
  isChild?: boolean;

  // Internal properties to store Field objects
  private _fieldObjects?: Field | Field[];

  constructor(field?: Field | Field[], fieldType?: FieldType, fieldMatchType?: RuleMatchType, value?: any,
              valueMatchType?: RuleMatchType, operator?: Operator, ruleForm?: FormGroup) {
    this.clazz = 'Rule';
    this.type = 'Rule';
    this._fieldObjects = field;

    // Convert Field objects to string array for ClientRule
    if (field) {
      if (field instanceof Array) {
        this.field = field.map(f => (f as Field).pathFromTransaction);
      } else {
        this.field = [(field as Field).pathFromTransaction];
      }
    }

    this.fieldType = fieldType as FieldTypeEnum;
    this.fieldMatchType = fieldMatchType;

    // Convert value to string array for ClientRule
    if (value) {
      if (value instanceof Array) {
        this.value = value.map(v => String(v));
      } else {
        this.value = [String(value)];
      }
    }

    this.valueMatchType = valueMatchType;
    this.operator = operator;
    this.ruleForm = ruleForm;
  }

  clone(): Rule {
    let rule: Rule = {...this};
    delete rule.ruleForm;

    if (this._fieldObjects) {
      if (this._fieldObjects instanceof Array) {
        rule._fieldObjects = this._fieldObjects.map((f: Field) => f.clone());
      } else if (this._fieldObjects instanceof Field) {
        rule._fieldObjects = this._fieldObjects.clone();
      }
    }
    return rule;
  }

  public isComplete(): boolean {
    if (!this.field || this.field.length === 0) {
      return false;
    }

    if (isEmptyString(this.fieldType)) {
      return false;
    }

    if (this.isEmptyOperator(this.operator)) {
      return false;
    }

    if (!this.value || this.value.length === 0) {
      return false;
    }

    if (this.valueMatchType == undefined) {
      return false;
    }
    if (this.fieldMatchType == undefined) {
      return false;
    }
    return true;
  }

  private isEmptyOperator(value: RuleOperator |Operator | undefined | null): boolean {
    return value === undefined || value === null;
  }

  // Getter for field objects
  getFieldObjects(): Field | Field[] | undefined {
    return this._fieldObjects;
  }

  // Setter for field objects
  setFieldObjects(field: Field | Field[]): void {
    this._fieldObjects = field;
    if (field instanceof Array) {
      this.field = field.map(f => (f as Field).pathFromTransaction);
    } else {
      this.field = [(field as Field).pathFromTransaction];
    }
  }
}

export interface Option {
  name: string;
  value: any;
}

export interface FieldMap {
  [key: string]: Field;
}


export class Field {

  name: string;
  pathFromTransaction: string;
  value?: string;
  type: string;
  nullable?: boolean;

  options?: Option[];
  operators?: Operator[];


  constructor(name: string, pathFromTransaction: string, type: string, value?: string, nullable?: boolean,
              options?: Option[], operators?: Operator[]) {
    this.name = name;
    this.pathFromTransaction = pathFromTransaction;
    this.value = value;
    this.type = type;
    this.nullable = nullable;
    this.options = options;
    this.operators = operators;
  }

  clone(): Field {

    let clone: Field = {...this};
    delete clone.nullable;
    delete clone.value;
    delete clone.options;
    delete clone.operators;

    return clone;

  }


  equals(field: Field): boolean {
    return this.name === field.name && this.type === field.type && this.value === field.value && this.nullable === field.nullable && this.options === field.options && this.operators === field.operators;
  }
}

export class MultiMap<K, V> {
  private map = new Map<K, V[]>();

  set(key: K, value: V): void {
    let values = this.map.get(key);
    if (values) {
      values.push(value);
    } else {
      this.map.set(key, [value]);
    }
  }

  get(key: K): V[] | undefined {
    return this.map.get(key);
  }

  has(key: K): boolean {
    return this.map.has(key);
  }

  delete(key: K): boolean {
    return this.map.delete(key);
  }

  clear(): void {
    this.map.clear();
  }

  keys(): K[] {
    return Array.from(this.map.keys());
  }
}


export interface LocalRuleMeta {
  ruleset: boolean;
  invalid: boolean;
}

export interface QueryBuilderClassNames {
  arrowIconButton?: string;
  arrowIcon?: string;
  removeIcon?: string;
  addIcon?: string;
  button?: string;
  buttonGroup?: string;
  removeButton?: string;
  removeButtonSize?: string;
  switchRow?: string;
  switchGroup?: string;
  switchLabel?: string;
  switchRadio?: string;
  switchControl?: string;
  rightAlign?: string;
  transition?: string;
  collapsed?: string;
  treeContainer?: string;
  tree?: string;
  row?: string;
  connector?: string;
  rule?: string;
  ruleSet?: string;
  invalidRuleSet?: string;
  emptyWarning?: string;
  fieldControl?: string;
  fieldControlSize?: string;
  operatorControl?: string;
  operatorControlSize?: string;
  inputControl?: string;
  inputControlSize?: string;
}

export interface QueryBuilderConfig {
  fields: FieldMap;
  allowEmptyRulesets?: boolean;


}

export const DEFAULT_QUERY_BUILDER_CONFIG: QueryBuilderConfig = {
  fields: {
    counterpartyName: new Field("counterpartyName", "counterparty.name", 'string', "Counterparty Name", undefined, undefined,
      StringOperators.ALL),
    counterpartyAccount: new Field("counterpartyAccount", "counterparty.accountNumber", 'string', "Counterparty Account", undefined,
      undefined, StringOperators.ALL),
    transaction: new Field("transaction", "transaction", 'string', "Transaction", undefined, undefined, StringOperators.ALL),
    communications: new Field("communications", "communications", 'string', "Communications", undefined, undefined,
      StringOperators.ALL),
    currency: new Field("currency", "currency", 'category', "Currency", undefined, [], CategoricalOperators.ALL),
    country: new Field("country", "countryCode", 'categorical', "Country", undefined, [], CategoricalOperators.ALL),
  }
}

function createFieldByNameMap(queryBuilderConfig: QueryBuilderConfig): Map<string, Field> {
  let map = new Map<string, Field>();
  for (let [key, value] of Object.entries(queryBuilderConfig.fields)) {
    map.set(value.name, value);
  }
  return map;

}

export const FIELDS_BY_NAME_MAP: Map<string, Field> = createFieldByNameMap(DEFAULT_QUERY_BUILDER_CONFIG);

function createFieldByPathFromTransactionMap(DEFAULT_QUERY_BUILDER_CONFIG: QueryBuilderConfig): Map<string, Field> {

  let map = new Map<string, Field>();
  for (let [key, value] of Object.entries(DEFAULT_QUERY_BUILDER_CONFIG.fields)) {
    map.set(value.pathFromTransaction, value);
  }
  return map;
}

export const FIELDS_BY_PATH_FROM_TRANSACTION_MAP: Map<string, Field> = createFieldByPathFromTransactionMap(DEFAULT_QUERY_BUILDER_CONFIG);

function createMatchTypesByNameMap(matchTypes: MatchTypeOption[]): Map<string, MatchTypeOption> {
  let map = new Map<string, MatchTypeOption>();
  for (let matchType of matchTypes) {
    map.set(matchType.name, matchType);
  }
  return map;
}

export const MATCH_TYPES_BY_NAME_MAP: Map<string, MatchTypeOption> = createMatchTypesByNameMap(MATCH_TYPES);


function ruleSetReviverFn0(key: string, value: any) {
  if (value && typeof value === 'object' && 'clazz' in value) {
    if (value.clazz === 'RuleSet') {
      return new RuleSet(value.condition, value.rules.map(ruleSetReviverFn0), value.collapsed, value.isChild);
    } else if (value.clazz === 'Rule') {
      // Revive the Operator object
      let operator = value.operator ? new Operator(value.operator.name, value.operator.value,
        value.operator.type) : undefined;

      // Revive the Field object(s)
      let field;
      if (Array.isArray(value.field)) {

        field = value.field.map((f: string) => FIELDS_BY_PATH_FROM_TRANSACTION_MAP.get(f));
      } else if (value.field) {
        field = FIELDS_BY_PATH_FROM_TRANSACTION_MAP.get(value.field);
      }

      return new Rule(field, value.fieldType, value.fieldMatchType, value.value, value.valueMatchType, operator);
    }
  }

  return value;
}

function ruleSetReviverFn(key: string, value: any) {
  if (value && typeof value === 'object' && 'clazz' in value) {
    if (value instanceof RuleSet) {
      return value;
    } else if (value instanceof Rule) {
      return value;
    }
    if (value.clazz === 'RuleSet') {
      let rules: Array<RuleSet | Rule> = [];
      if (Array.isArray(value.rules)) {
        rules = value.rules.map((ruleOrRuleSet: any) => {
          if (ruleOrRuleSet.clazz === 'RuleSet') {
            return ruleSetReviverFn('', ruleOrRuleSet);
          } else if (ruleOrRuleSet.clazz === 'Rule') {
            return ruleSetReviverFn('', ruleOrRuleSet);
          }
          return ruleOrRuleSet;
        });
      }

      return new RuleSet(value.condition, rules, value.collapsed, value.isChild);
    } else if (value.clazz === 'Rule') {
      // Revive the Operator object
      let operator = value.operator ? new Operator(value.operator.name, value.operator.value,
        value.operator.type) : undefined;

      // Revive the Field object(s)

      function allItemsAreStrings(arr: any[]): boolean {
        return arr.every((item: any) => typeof item === 'string');
      }

      let field;
      if (Array.isArray(value.field) && allItemsAreStrings(value.field)) {
        field = value.field.map((f: string) => {
          if (!FIELDS_BY_PATH_FROM_TRANSACTION_MAP.has(f)) {
            throw new Error(`Field ${f} not found in FIELDS_BY_PATH_FROM_TRANSACTION_MAP`);
          }
          return FIELDS_BY_PATH_FROM_TRANSACTION_MAP.get(f);
        });
      } else if (value.field && typeof value.field === 'string') {
        field = FIELDS_BY_PATH_FROM_TRANSACTION_MAP.get(value.field);
      }

      //revive the fieldMatchType
      let fieldMatchType: RuleMatchType | undefined;
      if (value.fieldMatchType && typeof value.fieldMatchType === 'string') {
        const matchTypeOption = MATCH_TYPES_BY_NAME_MAP.get(value.fieldMatchType);
        fieldMatchType = matchTypeOption?.value;
      } else {
        throw new Error('Invalid fieldMatchType');
      }

      let valueMatchType: RuleMatchType | undefined;
      if (value.valueMatchType && typeof value.valueMatchType === 'string') {
        const matchTypeOption = MATCH_TYPES_BY_NAME_MAP.get(value.valueMatchType);
        valueMatchType = matchTypeOption?.value;
      } else {
        throw new Error('Invalid valueMatchType');
      }


      return new Rule(field, value.fieldType, fieldMatchType, value.value, valueMatchType, operator);
    }
  }

  return value;
}


function operatorReviverFn(key: string, value: any): Operator {
  if (value && typeof value === 'object' && 'type' in value) {
    return new Operator(value.name, value.value, value.type);
  }
  return value;

}


function isValidRuleSetObject(obj: any): boolean {
  // Check if the object has the necessary properties
  if (!obj || !(obj instanceof RuleSet) || obj.clazz !== 'RuleSet' || !Array.isArray(obj.rules)) {
    return false;
  }

  // Check if each rule is a valid RuleSet or Rule object
  for (const rule of obj.rules) {
    if (rule instanceof RuleSet) {
      // If the rule is a RuleSet, check it recursively
      if (!isValidRuleSetObject(rule)) {
        return false;
      }
    } else if (rule instanceof Rule) {
      // If the rule is a Rule, check if it has the necessary properties

      if (!rule.field) {
        return false;
      } else if (Array.isArray(rule.field)) {
        if (!rule.field.every(f => typeof f === 'object' && f !== null && 'pathFromTransaction' in f)) {
          return false;
        }


      } else {
        if (!(typeof rule.field === 'object' && rule.field !== null && 'pathFromTransaction' in rule.field)) {
          return false;
        }
      }
      if (!rule.operator) {
        return false;
      } else {
        // Operator can be either an Operator instance or a string (RuleOperator)
        if (!(rule.operator instanceof Operator || typeof rule.operator === 'string')) {
          return false;
        }
      }
      if (!rule.value) {
        return false;
      }
      if (!rule.fieldMatchType) {
        return false;
      } else {
        if (!(rule.fieldMatchType && typeof rule.fieldMatchType === 'object' && 'name' in rule.fieldMatchType && 'value' in rule.fieldMatchType)) {
          return false;
        }
      }

      if (!rule.valueMatchType) {
        return false;
      } else {
        if (!(rule.valueMatchType && typeof rule.valueMatchType === 'object' && 'name' in rule.valueMatchType && 'value' in rule.valueMatchType)) {
          return false;
        }
      }
    } else {
      // If the rule is neither a RuleSet nor a Rule, return false
      return false;
    }
  }

  // If all checks passed, return true
  return true;
}

export function deserializeRuleSet(jsonString: string): RuleSet {
  let ruleSet = JSON.parse(jsonString, ruleSetReviverFn);
  if (!isValidRuleSetObject(ruleSet)) {
    throw new Error('Invalid RuleSet object');

  }
  return ruleSet;
}


export class Comparator {


  private isUndefinedOrNull(o: any): boolean {
    return o === undefined || o === null;
  }


  public equals(o1: any, o2: any): boolean {
    if (this.isUndefinedOrNull(o1) && this.isUndefinedOrNull(o2)) {
      return true;
    }
    if (this.bothAreArrays(o1, o2)) {
      return this.checkArraysAreEqual(o1, o2);
    }
    if (this.isObject(o1) && this.isObject(o2)) {
      return this.objectsAreEqual(o1, o2);
    }

    return o1 === o2;

  }

  private checkArraysAreEqual(arr1: any[], arr2: any[]): boolean {

    //check if all items in o1 and o2 have the same typeof
    if (arr1.length !== arr2.length) {
      return false;
    }
    const sortedList1 = arr1.sort();
    const sortedList2 = arr2.sort();
    for (let i = 0; i < arr1.length; i++) {
      let item1 = sortedList1[i];
      let item2 = sortedList2[i];
      if (typeof item1 !== typeof item2) {
        throw new Error(`Unexpected type: ${typeof item1} and ${typeof item2} are not the same type`);
      }

      if(isObject(item1) && isObject(item2)){
        if(!objectsAreEqual(item1, item2)){
          return false;
        }
      }
    }

    return true;
  }

  private bothAreArrays(o1: any, o2: any): boolean {
    return Array.isArray(o1) && Array.isArray(o2);
  }

  private isObject(object: any): boolean {
    return object != null && typeof object === 'object';
  }

  private objectsAreEqual(obj1: any, obj2: any): boolean {
    // Get the keys
    const keys1 = Object.keys(obj1);
    const keys2 = Object.keys(obj2);

    // If number of keys is different,
    // then objects are not equal
    if (keys1.length !== keys2.length) {
      return false;
    }

    // Iterate over keys
    for (const key of keys1) {
      const val1 = obj1[key];
      const val2 = obj2[key];
      const areObjects = isObject(val1) && isObject(val2);
      if ((areObjects && !this.objectsAreEqual(val1, val2)) || (!areObjects && val1 !== val2)) {
        return false;
      }
    }

    return true;
  }

}

// Conversion functions to convert between the project's interfaces and the interfaces from @daanvdn/budget-assistant-client

/**
 * Converts a Rule to a ClientRule
 */
export function convertRuleToClientRule(rule: Rule, type: string = 'BOTH'): ClientRule {
  const operatorValue = rule.operator instanceof Operator ? rule.operator.value : rule.operator;
  return {
    field: rule.field.join('.'),
    fieldType: rule.fieldType,
    value: rule.value instanceof Array
      ? rule.value.map(v => String(v)).join(',')
      : String(rule.value),
    operator: operatorValue as RuleOperator
  };
}

/**
 * Converts a RuleSet to a ClientRuleSet
 */
/*
export function convertRuleSetToClientRuleSet(ruleSet: RuleSet, type: TypeEnum = TypeEnum.BOTH): ClientRuleSet {
  return {
    clazz: ruleSet.clazz,
    type: type,
    condition: ruleSet.condition as ConditionEnum,
    rules: ruleSet.rules.map(rule => {
      if (rule instanceof RuleSet) {
        return convertRuleSetToClientRuleSet(rule, type);
      } else {
        return convertRuleToClientRule(rule as Rule, type);
      }
    }),
    isChild: ruleSet.isChild === undefined ? false : ruleSet.isChild
  };
}
*/

/**
 * Converts a RuleSetWrapper to a ClientRuleSetWrapper
 */

/**
 * Converts a ClientRule to a Rule
 */
export function convertClientRuleToRule(clientRule: ClientRule): Rule {
  const rule = new Rule();
  rule.clazz = (clientRule as any).clazz || 'Rule';
  // Handle field - it's a string in the new API
  if (typeof clientRule.field === 'string') {
    rule.field = clientRule.field.split('.');
  }
  if (clientRule.fieldType) {
    rule.fieldType = clientRule.fieldType;
  }
  // Handle value - it could be a string or undefined
  if (clientRule.value) {
    rule.value = typeof clientRule.value === 'string' ? clientRule.value.split(',') : [String(clientRule.value)];
  }
  rule.valueMatchType = (clientRule as any).valueMatchType;
  rule.operator = clientRule.operator;
  return rule;
}

/**
 * Converts a ClientRuleSet to a RuleSet
 */
export function convertClientRuleSetToRuleSet(clientRuleSet: ClientRuleSet | { [key: string]: any }): RuleSet {
  // Handle empty or invalid input
  if (!clientRuleSet || !clientRuleSet.condition) {
    return new RuleSet('AND', [], false, false);
  }

  const ruleSet = new RuleSet(
    clientRuleSet.condition,
    [],
    false,
    (clientRuleSet as any).isChild
  );

  if (clientRuleSet.rules && Array.isArray(clientRuleSet.rules)) {
    ruleSet.rules = clientRuleSet.rules.map((rule: any) => {
      if (rule.clazz === 'RuleSet' || (rule.condition && rule.rules)) {
        return convertClientRuleSetToRuleSet(rule as ClientRuleSet);
      } else {
        return convertClientRuleToRule(rule as ClientRule);
      }
    });
  }

  return ruleSet;
}

/**
 * Converts a ClientRuleSetWrapper to a RuleSetWrapper
 */
