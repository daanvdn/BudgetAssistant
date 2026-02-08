/**
 * Zod schemas for the RuleSet / Rule API data shape.
 *
 * These schemas define the exact JSON structure expected by the Python/Pydantic backend,
 * using **camelCase** keys (the CaseConverterInterceptor handles camelCase → snake_case
 * conversion on the wire).
 *
 * Two main entry points:
 *   ruleSetToApi(ruleSet)  — UI RuleSet → validated plain object for the API
 *   ruleSetFromApi(data)   — API response data → validated & hydrated UI RuleSet
 */

import {z} from 'zod';
import {
    FieldTypeEnum,
    FIELDS_BY_PATH_FROM_TRANSACTION_MAP,
    MATCH_TYPES_BY_NAME_MAP,
    Operator,
    Rule,
    RuleMatchType,
    RuleSet,
    RuleUtils,
} from './rule-commons.interfaces';

// ═══════════════════════════════════════════════════════════════════
//  Primitive / enum schemas
// ═══════════════════════════════════════════════════════════════════

/** Must match Python TransactionTypeEnum. */
export const TransactionTypeSchema = z.enum(['REVENUE', 'EXPENSES', 'BOTH']);
export type TransactionType = z.infer<typeof TransactionTypeSchema>;

const ConditionSchema = z.enum(['AND', 'OR']);

/** Must match Python FieldType literal. */
const FieldTypeSchema = z.enum(['number', 'string', 'categorical']);

/** Must match Python MatchTypeOptions literal. */
const MatchTypeOptionsSchema = z.enum(['any of', 'all of']);

// ═══════════════════════════════════════════════════════════════════
//  Nested-object schemas
// ═══════════════════════════════════════════════════════════════════

/** Matches Python RuleMatchType(BaseModel): {name, value}. */
const RuleMatchTypeSchema = z.object({
    name: MatchTypeOptionsSchema,
    value: MatchTypeOptionsSchema,
});

/**
 * Matches Python RuleOperator(BaseModel): {name, value, type}.
 *
 * `name` is kept as z.string() (lenient) rather than a strict OperatorName enum
 * so that frontend-specific operator names (e.g. categorical 'in' / 'not in')
 * pass frontend validation and are caught by the backend if invalid.
 */
const RuleOperatorSchema = z.object({
    name: z.string(),
    value: z.string(),
    type: FieldTypeSchema,
});

// ═══════════════════════════════════════════════════════════════════
//  Rule schema (API shape, camelCase)
// ═══════════════════════════════════════════════════════════════════

export const ApiRuleSchema = z.object({
    clazz: z.literal('Rule'),
    type: TransactionTypeSchema,
    field: z.array(z.string()),          // List[TransactionField]
    fieldType: FieldTypeSchema,          // FieldType
    value: z.array(z.union([z.string(), z.number()])),
    valueMatchType: RuleMatchTypeSchema, // nested object, NOT a plain string
    operator: RuleOperatorSchema,        // nested object, NOT a plain string
    // fieldMatchType is frontend-only — not in the Python model but preserved
    // in the stored JSON for round-trip compatibility.
    fieldMatchType: RuleMatchTypeSchema.optional(),
});

export type ApiRule = z.infer<typeof ApiRuleSchema>;

// ═══════════════════════════════════════════════════════════════════
//  RuleSet schema (recursive, API shape, camelCase)
// ═══════════════════════════════════════════════════════════════════

export type ApiRuleSet = {
    clazz: 'RuleSet';
    type: TransactionType;
    condition: 'AND' | 'OR';
    rules: Array<ApiRule | ApiRuleSet>;
    isChild: boolean;
};

export const ApiRuleSetSchema: z.ZodType<ApiRuleSet> = z.object({
    clazz: z.literal('RuleSet'),
    type: TransactionTypeSchema,
    condition: ConditionSchema,
    rules: z.array(z.lazy(() => z.union([ApiRuleSchema, ApiRuleSetSchema]))),
    isChild: z.boolean(),
});

// ═══════════════════════════════════════════════════════════════════
//  toApi  —  UI RuleSet → validated API plain object
// ═══════════════════════════════════════════════════════════════════

/**
 * Convert a UI match-type value (short 'any'/'all', MatchTypeOption object,
 * or full 'any of'/'all of') to the API object form {name, value}.
 */
function resolveMatchType(mt: any): {name: string; value: string} {
    if (!mt) return {name: 'any of', value: 'any of'};
    if (typeof mt === 'object' && 'name' in mt && 'value' in mt) {
        // Already an object — normalise name to the "x of" form
        const n = String(mt.name);
        const mapped = n === 'any' ? 'any of' : n === 'all' ? 'all of' : n;
        return {name: mapped, value: mapped};
    }
    const s = String(mt);
    if (s === 'any' || s === 'any of') return {name: 'any of', value: 'any of'};
    if (s === 'all' || s === 'all of') return {name: 'all of', value: 'all of'};
    return {name: s, value: s};
}

/**
 * Convert a UI Operator (instance, plain object, or string) to API object form
 * {name, value, type}.
 */
function resolveOperator(op: any, fieldType?: string): {name: string; value: string; type: string} {
    if (!op) return {name: '', value: '', type: fieldType || 'string'};
    if (op instanceof Operator) return {name: op.name, value: op.value, type: op.type};
    if (typeof op === 'object' && 'name' in op) {
        return {name: op.name, value: op.value || op.name, type: op.type || fieldType || 'string'};
    }
    const s = String(op);
    return {name: s, value: s, type: fieldType || 'string'};
}

/**
 * Convert a UI Rule to API shape and validate with Zod.
 * @param rule       The UI Rule instance.
 * @param parentType Fallback TransactionType inherited from a parent RuleSet.
 */
export function ruleToApi(rule: Rule, parentType?: string): ApiRule {
    const raw = {
        clazz: 'Rule' as const,
        type: rule.type || parentType || 'BOTH',
        field: rule.field,
        fieldType: rule.fieldType || 'string',
        value: rule.value,
        valueMatchType: resolveMatchType(rule.valueMatchType),
        operator: resolveOperator(rule.operator, rule.fieldType),
        fieldMatchType: resolveMatchType(rule.fieldMatchType),
    };
    return ApiRuleSchema.parse(raw);
}

/**
 * Convert a UI RuleSet (including all nested rules / child RuleSets) to
 * API shape and validate with Zod.
 */
export function ruleSetToApi(ruleSet: RuleSet): ApiRuleSet {
    const type = ruleSet.type || 'BOTH';
    const raw = {
        clazz: 'RuleSet' as const,
        type,
        condition: ruleSet.condition as 'AND' | 'OR',
        rules: (ruleSet.rules || []).map((item: any) => {
            if (RuleUtils.isRuleSet(item)) {
                // Propagate type from parent when child doesn't carry one
                if (!item.type) item.type = type;
                return ruleSetToApi(item as RuleSet);
            }
            return ruleToApi(item as Rule, type);
        }),
        isChild: ruleSet.isChild ?? false,
    };
    return ApiRuleSetSchema.parse(raw);
}

// ═══════════════════════════════════════════════════════════════════
//  fromApi  —  API data → validated & hydrated UI RuleSet
// ═══════════════════════════════════════════════════════════════════

/** Map an API match-type name ('any of' | 'all of') to the short UI form ('any' | 'all'). */
function toUiMatchType(name: string): RuleMatchType {
    const option = MATCH_TYPES_BY_NAME_MAP.get(name);
    return option?.value ?? 'any';
}

function hydrateRule(data: ApiRule): Rule {
    const rule = new Rule();
    rule.field = [...data.field];
    rule.fieldType = data.fieldType as FieldTypeEnum;
    rule.value = data.value.map(v => String(v));
    rule.operator = new Operator(data.operator.name, data.operator.value, data.operator.type as FieldTypeEnum);
    rule.valueMatchType = toUiMatchType(data.valueMatchType.name);
    rule.fieldMatchType = data.fieldMatchType
        ? toUiMatchType(data.fieldMatchType.name)
        : 'any';
    rule.type = data.type;

    // Best-effort: hydrate Field objects so the pill editor can display them
    const fields = data.field
        .map(f => FIELDS_BY_PATH_FROM_TRANSACTION_MAP.get(f))
        .filter((f): f is NonNullable<typeof f> => f !== undefined);
    if (fields.length > 0) {
        rule.setFieldObjects(fields.length === 1 ? fields[0] : fields);
    }

    return rule;
}

function hydrateRuleSet(data: ApiRuleSet): RuleSet {
    const rules = data.rules.map(item =>
        item.clazz === 'RuleSet'
            ? hydrateRuleSet(item as ApiRuleSet)
            : hydrateRule(item as ApiRule),
    );
    const rs = new RuleSet(data.condition, rules, false, data.isChild);
    rs.type = data.type;
    return rs;
}

/**
 * Validate API data with Zod and hydrate into a UI RuleSet.
 * Throws ZodError if validation fails.
 */
export function ruleSetFromApi(data: unknown): RuleSet {
    const validated = ApiRuleSetSchema.parse(data);
    return hydrateRuleSet(validated);
}

/**
 * Safely attempt to parse API data. Returns null if validation fails, logging
 * the Zod error to the console.
 */
export function ruleSetFromApiSafe(data: unknown): RuleSet | null {
    const result = ApiRuleSetSchema.safeParse(data);
    if (!result.success) {
        console.error('[RuleSchema] Validation failed:', result.error.format());
        return null;
    }
    return hydrateRuleSet(result.data);
}
