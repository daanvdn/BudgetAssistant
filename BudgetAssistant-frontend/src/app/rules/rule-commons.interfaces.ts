import {FormGroup} from "@angular/forms";

// Define local types that were previously imported from the client
export type RuleMatchType = 'all' | 'any';
export type RuleOperator =
    'eq'
    | 'ne'
    | 'gt'
    | 'gte'
    | 'lt'
    | 'lte'
    | 'contains'
    | 'not_contains'
    | 'starts_with'
    | 'ends_with'
    | 'is_null'
    | 'is_not_null'
    | 'in'
    | 'not_in';
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

    public asOperator(): RuleOperator {
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
    static CONTAINS = new Operator('contains', 'contains', 'categorical');
    static EXACT_MATCH = new Operator('exact match', 'exact match', 'categorical');
    static ALL: Operator[] = [CategoricalOperators.CONTAINS, CategoricalOperators.EXACT_MATCH];
}

export class NumericalOperators {
    // value = name to match Python's RuleOperator.create() pattern
    static EQUALS = new Operator('equals', 'equals', 'number');
    static NOT_EQUALS = new Operator('not equals', 'not equals', 'number');
    static GREATER_THAN = new Operator('greater than', 'greater than', 'number');
    static GREATER_THAN_OR_EQUALS = new Operator('greater than or equals', 'greater than or equals', 'number');
    static LESS_THAN = new Operator('less than', 'less than', 'number');
    static LESS_THAN_OR_EQUALS = new Operator('less than or equals', 'less than or equals', 'number');
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
            }
            else if (rule instanceof Rule) {
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
            }
            else if ((item as any) instanceof Rule) {
                if (!(item as Rule).isComplete()) {
                    return false;
                }
            }
        }

        return true;
    }

}


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
            if (rule.operator !== undefined && op && op.equals(CategoricalOperators.EXACT_MATCH)) {
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
        this._fieldObjects = field;

        // Convert Field objects to string array for ClientRule
        if (field) {
            if (field instanceof Array) {
                this.field = field.map(f => (f as Field).pathFromTransaction);
            }
            else {
                this.field = [(field as Field).pathFromTransaction];
            }
        }

        this.fieldType = fieldType as FieldTypeEnum;
        this.fieldMatchType = fieldMatchType;

        // Convert value to string array for ClientRule
        if (value) {
            if (value instanceof Array) {
                this.value = value.map(v => String(v));
            }
            else {
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
            }
            else if (this._fieldObjects instanceof Field) {
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

    private isEmptyOperator(value: RuleOperator | Operator | undefined | null): boolean {
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
        }
        else {
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

export interface QueryBuilderConfig {
    fields: FieldMap;
    allowEmptyRulesets?: boolean;


}

export const DEFAULT_QUERY_BUILDER_CONFIG: QueryBuilderConfig = {
    fields: {
        counterpartyName: new Field("counterpartyName", "counterparty.name", 'string', "Counterparty Name", undefined,
            undefined,
            StringOperators.ALL),
        counterpartyAccount: new Field("counterpartyAccount", "counterparty.account_number", 'string',
            "Counterparty Account", undefined,
            undefined, StringOperators.ALL),
        transaction: new Field("transaction", "transaction", 'string', "Transaction", undefined, undefined,
            StringOperators.ALL),
        communications: new Field("communications", "communications", 'string', "Communications", undefined, undefined,
            StringOperators.ALL),
        currency: new Field("currency", "currency", 'category', "Currency", undefined, [], CategoricalOperators.ALL),
        country: new Field("country", "country_code", 'categorical', "Country", undefined, [], CategoricalOperators.ALL),
    }
}

function createFieldByPathFromTransactionMap(DEFAULT_QUERY_BUILDER_CONFIG: QueryBuilderConfig): Map<string, Field> {

    let map = new Map<string, Field>();
    for (let [key, value] of Object.entries(DEFAULT_QUERY_BUILDER_CONFIG.fields)) {
        map.set(value.pathFromTransaction, value);
    }
    return map;
}

export const FIELDS_BY_PATH_FROM_TRANSACTION_MAP: Map<string, Field> = createFieldByPathFromTransactionMap(
    DEFAULT_QUERY_BUILDER_CONFIG);

function createMatchTypesByNameMap(matchTypes: MatchTypeOption[]): Map<string, MatchTypeOption> {
    let map = new Map<string, MatchTypeOption>();
    for (let matchType of matchTypes) {
        map.set(matchType.name, matchType);
    }
    return map;
}

export const MATCH_TYPES_BY_NAME_MAP: Map<string, MatchTypeOption> = createMatchTypesByNameMap(MATCH_TYPES);

