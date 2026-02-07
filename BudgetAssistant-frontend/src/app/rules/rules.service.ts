import { Injectable, inject } from '@angular/core';
import { Observable, catchError, throwError, retry, timer } from 'rxjs';
import { BudgetAssistantApiService } from '@daanvdn/budget-assistant-client';
import {
    RuleSetWrapperRead, RuleSetWrapperCreate,
    CategorizeTransactionsResponse,
    TransactionTypeEnum, SuccessResponse,
    GetOrCreateRuleSetWrapperRequest,
    RuleSet,
} from './rule.models';
import {ruleSetToApi, ruleSetFromApi} from './rule-api.schemas';

@Injectable({ providedIn: 'root' })
export class RulesService {
    private api = inject(BudgetAssistantApiService);

    /** Standardized error handler for API calls */
    private handleError(operation: string) {
        return (error: any): Observable<never> => {
            const message = error?.error?.detail
                || error?.message
                || `${operation} failed`;
            console.error(`[RulesService] ${operation}:`, error);
            return throwError(() => new Error(message));
        };
    }

    /**
     * Get or create a RuleSetWrapper for a category.
     */
    getOrCreateRuleSetWrapper(
        categoryQualifiedName: string,
        type: TransactionTypeEnum
    ): Observable<RuleSetWrapperRead> {
        const request: GetOrCreateRuleSetWrapperRequest = {
            categoryQualifiedName,
            type
        };
        return this.api.rules.getOrCreateRuleSetWrapperApiRulesGetOrCreatePost(request).pipe(
            retry({ count: 1, delay: (_, retryCount) => timer(retryCount * 1000) }),
            catchError(this.handleError('Get or create rule set'))
        );
    }

    /**
     * Save a RuleSetWrapper with an updated rule set.
     */
    saveRuleSetWrapper(
        categoryId: number,
        ruleSet: RuleSet
    ): Observable<SuccessResponse> {
        const serialized = this.serializeRuleSet(ruleSet);
        const body: RuleSetWrapperCreate = {
            categoryId,
            ruleSet: serialized
        };
        return this.api.rules.saveRuleSetWrapperApiRulesSavePost(body).pipe(
            catchError(this.handleError('Save rule set'))
        );
    }

    /**
     * Run categorization on all transactions.
     */
    categorizeTransactions(): Observable<CategorizeTransactionsResponse> {
        return this.api.rules.categorizeTransactionsApiRulesCategorizeTransactionsPost().pipe(
            catchError(this.handleError('Categorize transactions'))
        );
    }

    /**
     * Parse a RuleSetWrapperRead's ruleSet JSON blob into a typed RuleSet.
     * Validates the data with Zod before hydrating UI classes.
     */
    parseRuleSet(wrapper: RuleSetWrapperRead): RuleSet {
        return ruleSetFromApi(wrapper.ruleSet);
    }

    /**
     * Serialize a typed RuleSet to a validated plain object for the API.
     * Uses Zod to ensure the output matches the Pydantic backend model.
     */
    serializeRuleSet(ruleSet: RuleSet): { [key: string]: any } {
        return ruleSetToApi(ruleSet);
    }

    /**
     * Save using a pre-serialized RuleSetWrapperCreate body.
     * Used by the pill editor dialog which handles its own serialization.
     */
    saveRuleSetWrapperDirect(body: RuleSetWrapperCreate): Observable<SuccessResponse> {
        return this.api.rules.saveRuleSetWrapperApiRulesSavePost(body).pipe(
            catchError(this.handleError('Save rule set'))
        );
    }
}
