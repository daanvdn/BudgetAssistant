import {FormGroup} from "@angular/forms";

import {CategoryType} from "../model";


export type FieldType = 'string' | 'number' | 'categorical' | 'null';


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

export class Operator {
  readonly name: string;
  readonly value: string;
  readonly type: FieldType;


  constructor(name: string, value: string, fieldType: FieldType) {
    this.value = value;
    this.type = fieldType;
    this.name = name;
  }

  equals(operator: Operator): boolean {
    return this.value === operator.value && this.type === operator.type && this.name === operator.name;
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


export class RuleSet {

  clazz: string;
  condition: string;
  rules: Array<RuleSet | Rule | any>;
  collapsed?: boolean;
  isChild?: boolean;


  constructor(condition: string, rules: Array<any>, collapsed?: boolean, isChild?: boolean) {
    this.clazz = 'RuleSet';
    this.condition = condition;
    this.rules = rules;
    this.collapsed = collapsed;
    this.isChild = isChild;
  }


  public clone(): RuleSet {
    let clone: RuleSet = {...this};
    delete clone.collapsed;
    delete clone.isChild;

    clone.rules = clone.rules.map((rule: RuleSet | Rule) => {
      if (rule instanceof RuleSet) {
        return rule.clone();
      } else {
        return rule.clone();
      }
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
      if (item instanceof RuleSet) {
        if (!item.isComplete()) {
          return false;
        }
      } else {
        if (!item.isComplete()) {
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
        return value.pathFromTransaction;
      }
      if (key === 'field' && value instanceof Array) {
        return value.map((f: Field) => f.pathFromTransaction);

      }
      if (value instanceof MatchType) {
        return value.name;
      }

      return value;

    }


    return JSON.stringify(clone, mapper);
  }


}


export interface RuleSetWrapper {
  id?: number;
  category: string;
  categoryType: CategoryType;
  ruleSet: RuleSet;
  users: string[]
}

// export type MatchType = 'any of' | 'all of';


export class MatchType {
  readonly name: string;
  readonly value: string;


  constructor(name: string, value: string) {
    this.name = name;
    this.value = value;
  }

  equals(matchType: MatchType): boolean {
    return this.name === matchType.name && this.value === matchType.value;
  }
}


export class MatchTypes {
  static ANY_OF = new MatchType('any of', 'any of');
  static ALL_OF = new MatchType('all of', 'all of');
  static ALL: MatchType[] = [MatchTypes.ANY_OF, MatchTypes.ALL_OF];
}

export const MATCH_TYPES: MatchType[] = MatchTypes.ALL;

export class RuleUtils {


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
    if (rule.fieldType !== undefined && (rule.fieldType === 'null')) {
      return true;
    }
    if (rule.fieldType !== undefined && rule.fieldType === 'categorical') {
      if (rule.operator !== undefined && rule.operator === CategoricalOperators.EQUALS) {
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


export class Rule {

  clazz: string;
  field?: Field | Field[];
  fieldType?: FieldType;

  fieldMatchType?: MatchType;

  value?: any | Array<any>;

  valueMatchType?: MatchType;
  operator?: Operator;
  ruleForm?: FormGroup;

  constructor(field?: Field | Field[], fieldType?: FieldType, fieldMatchType?: MatchType, value?: any,
              valueMatchType?: MatchType, operator?: Operator, ruleForm?: FormGroup) {
    this.clazz = 'Rule';
    this.field = field;
    this.fieldType = fieldType;
    this.fieldMatchType = fieldMatchType;
    this.value = value;
    this.valueMatchType = valueMatchType;
    this.operator = operator;
    this.ruleForm = ruleForm;
  }

  clone(): Rule {
    let rule: Rule = {...this};
    delete rule.ruleForm;

    if (rule.field && rule.field instanceof Array) {
      rule.field = rule.field.map((f: Field) => f.clone());
    } else if (rule.field) {
      rule.field = rule.field.clone();
    }
    return rule;
  }


  public isComplete(): boolean {
    if (!this.field || (this.field instanceof Array && this.field.length === 0)) {
      return false;
    }

    if (isEmptyString(this.fieldType)) {
      return false;
    }


    if (this.isEmptyOperator(this.operator)) {
      return false;
    }

    if (!this.value || (this.value instanceof Array && this.value.length === 0)) {
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

  private isEmptyOperator(value: Operator | undefined | null): boolean {

    return value === undefined || value === null;

  }

  /*public toJson(): string {
    if (!this.isComplete()) {
      throw new Error('RuleSet is not complete');
    }
    let json = serialize(this);

    // Post-process the serialized JSON to remove properties that are undefined
    return JSON.parse(JSON.stringify(json, (key, value) => value === undefined ? undefined : value));


  }*/
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

function createMatchTypesByNameMap(MATCH_TYPES: MatchType[]): Map<string, MatchType> {
  let map = new Map<string, MatchType>();
  for (let matchType of MATCH_TYPES) {
    map.set(matchType.name, matchType);
  }
  return map;
}

export const MATCH_TYPES_BY_NAME_MAP: Map<string, MatchType> = createMatchTypesByNameMap(MATCH_TYPES);


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
      let fieldMatchType;
      if (value.fieldMatchType && typeof value.fieldMatchType === 'string') {
        fieldMatchType = MATCH_TYPES_BY_NAME_MAP.get(value.fieldMatchType);
      } else {
        throw new Error('Invalid fieldMatchType');
      }

      let valueMatchType;
      if (value.valueMatchType && typeof value.valueMatchType === 'string') {
        valueMatchType = MATCH_TYPES_BY_NAME_MAP.get(value.fieldMatchType);
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
        if (!rule.field.every(f => f instanceof Field)) {
          return false;
        }


      } else {
        if (!(rule.field instanceof Field)) {
          return false;
        }
      }
      if (!rule.operator) {
        return false;
      } else {
        if (!(rule.operator instanceof Operator)) {
          return false;
        }
      }
      if (!rule.value) {
        return false;
      }
      if (!rule.fieldMatchType) {
        return false;
      } else {
        if (!(rule.fieldMatchType instanceof MatchType)) {
          return false;
        }
      }

      if (!rule.valueMatchType) {
        return false;
      } else {
        if (!(rule.valueMatchType instanceof MatchType)) {
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
