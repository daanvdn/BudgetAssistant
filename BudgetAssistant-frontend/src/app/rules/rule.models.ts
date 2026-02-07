// Re-export core rule model types from query-builder
export {
    RuleSet, Rule, Field, Operator, FieldMap,
    StringOperators, CategoricalOperators, NumericalOperators,
    MatchTypes, MatchTypeOption, MATCH_TYPES,
    DEFAULT_QUERY_BUILDER_CONFIG, FIELDS_BY_PATH_FROM_TRANSACTION_MAP,
    RuleUtils, QueryBuilderConfig
} from './query-builder.interfaces';

// Re-export Zod-based API serialization / deserialization
export {ruleSetToApi, ruleSetFromApi, ruleSetFromApiSafe} from './rule-api.schemas';

// Re-export API types from client library
export {
    RuleSetWrapperRead, RuleSetWrapperCreate,
    CategorizeTransactionsResponse, CategoryRead,
    TransactionTypeEnum, SuccessResponse,
    GetOrCreateRuleSetWrapperRequest
} from '@daanvdn/budget-assistant-client';

import {
    Field, NumericalOperators, CategoricalOperators,
    DEFAULT_QUERY_BUILDER_CONFIG, FIELDS_BY_PATH_FROM_TRANSACTION_MAP,
    RuleSet, Rule, RuleUtils, QueryBuilderConfig
} from './query-builder.interfaces';

// Register extended fields (amount, fixed currency) into the shared lookup map
// so that ruleSetFromApi() can hydrate Field objects for all known fields.
const _extendedFields: Record<string, Field> = {
    amount: new Field('amount', 'amount', 'number', 'Amount', undefined, undefined, NumericalOperators.ALL),
    currency: new Field('currency', 'currency', 'categorical', 'Currency', undefined, [], CategoricalOperators.ALL),
};
for (const field of Object.values(_extendedFields)) {
    if (!FIELDS_BY_PATH_FROM_TRANSACTION_MAP.has(field.pathFromTransaction)) {
        FIELDS_BY_PATH_FROM_TRANSACTION_MAP.set(field.pathFromTransaction, field);
    }
}

// ---------------------------------------------------------------------------
// New types for the pill-editor / summary UI
// ---------------------------------------------------------------------------

/** Represents one node in a human-readable rule summary tree */
export interface SummaryNode {
    text: string;              // e.g. 'counterparty name contains "Carrefour" or "Colruyt"'
    children?: SummaryNode[];  // for nested RuleSets
    isGroup?: boolean;
    condition?: 'AND' | 'OR';
}

// ---------------------------------------------------------------------------
// Extended field config (adds `amount`, fixes `currency` type)
// ---------------------------------------------------------------------------

export const RULE_FIELDS_CONFIG: QueryBuilderConfig = {
    ...DEFAULT_QUERY_BUILDER_CONFIG,
    fields: {
        ...DEFAULT_QUERY_BUILDER_CONFIG.fields,
        // Add amount field (type: 'number', with all numerical operators)
        amount: new Field('amount', 'amount', 'number', 'Amount', undefined, undefined, NumericalOperators.ALL),
        // Override currency to fix type from 'category' to 'categorical'
        currency: new Field('currency', 'currency', 'categorical', 'Currency', undefined, [], CategoricalOperators.ALL),
    }
};

// ---------------------------------------------------------------------------
// Summary rendering helpers
// ---------------------------------------------------------------------------

/**
 * Resolve a field path (e.g. "counterparty.name") to a human-readable name.
 * Falls back to the raw path when no mapping is found.
 */
function resolveFieldName(fieldPath: string): string {
    const field = FIELDS_BY_PATH_FROM_TRANSACTION_MAP.get(fieldPath);
    return field?.value ?? field?.name ?? fieldPath;
}

/**
 * Build a human-readable text representation of a single Rule.
 * Example: 'Counterparty Name contains "Carrefour" or "Colruyt"'
 */
function ruleSummaryText(rule: Rule): string {
    // Field name(s)
    const fieldNames = (rule.field ?? []).map(f => resolveFieldName(f));
    const fieldPart = fieldNames.length > 1
        ? fieldNames.join(', ')
        : (fieldNames[0] ?? '?');

    // Operator
    const operatorName = rule.operator
        ? (typeof rule.operator === 'object' && 'name' in rule.operator
            ? (rule.operator as { name: string }).name
            : String(rule.operator))
        : '?';

    // Value(s) — cap display at 3 items for readability
    const values = rule.value ?? [];
    let valuePart: string;
    if (values.length === 0) {
        valuePart = '(no value)';
    } else if (values.length <= 3) {
        valuePart = values.map(v => `"${v}"`).join(' or ');
    } else {
        const shown = values.slice(0, 3).map(v => `"${v}"`).join(', ');
        valuePart = `${shown} (+${values.length - 3} more)`;
    }

    return `${fieldPart} ${operatorName} ${valuePart}`;
}

/** Maximum nesting depth shown in summaries before truncating with "…" */
const MAX_SUMMARY_DEPTH = 3;

/**
 * Convert a RuleSet into a tree of human-readable summary nodes.
 * Used by RuleSummaryCardComponent to render the read-only view.
 * Caps display depth at MAX_SUMMARY_DEPTH to avoid overly nested UIs.
 */
export function ruleSetToSummary(ruleSet: RuleSet, depth: number = 0): SummaryNode {
    if (!ruleSet || !ruleSet.rules || ruleSet.rules.length === 0) {
        return { text: '(no rules)' };
    }

    // Cap depth — show ellipsis for deeply nested groups
    if (depth >= MAX_SUMMARY_DEPTH) {
        return { text: '(…nested rules)' };
    }

    const children: SummaryNode[] = ruleSet.rules.map((item: any) => {
        if (RuleUtils.isRuleSet(item)) {
            return ruleSetToSummary(item as RuleSet, depth + 1);
        }
        if (RuleUtils.isRule(item)) {
            return { text: ruleSummaryText(item as Rule) };
        }
        // Fallback for unrecognised shapes
        return { text: String(item) };
    });

    return {
        text: '',
        isGroup: true,
        condition: ruleSet.condition as 'AND' | 'OR',
        children
    };
}

/**
 * Convert a RuleSet into a single flat string (for search, chips, etc.)
 */
export function ruleSetToString(ruleSet: RuleSet): string {
    const node = ruleSetToSummary(ruleSet);
    return flattenNode(node);
}

function flattenNode(node: SummaryNode): string {
    if (!node.isGroup || !node.children || node.children.length === 0) {
        return node.text;
    }
    const joiner = ` ${node.condition ?? 'AND'} `;
    const parts = node.children.map(c => flattenNode(c));
    return parts.length > 1 ? `(${parts.join(joiner)})` : parts[0];
}
