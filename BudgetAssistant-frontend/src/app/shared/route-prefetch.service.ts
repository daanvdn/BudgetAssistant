import {inject, Injectable} from '@angular/core';
import {QueryClient} from '@tanstack/angular-query-experimental';
import {firstValueFrom} from 'rxjs';
import {
  BudgetAssistantApiService,
  BudgetTreeCreate,
  PageTransactionsRequest,
  PageUncategorizedTransactionsRequest,
  SortOrder,
  TransactionSortProperty,
  TransactionTypeEnum
} from '@daanvdn/budget-assistant-client';
import {AppService} from '../app.service';
import {RulesService} from '../rules/rules.service';

/**
 * Prefetches TanStack Query data on navigation‐link hover so that
 * the target route's component can render cached data instantly.
 */
@Injectable({providedIn: 'root'})
export class RoutePrefetchService {
  private readonly queryClient = inject(QueryClient);
  private readonly apiService = inject(BudgetAssistantApiService);
  private readonly appService = inject(AppService);
  private readonly rulesService = inject(RulesService);

  // ── /transacties ──────────────────────────────────────────────────────
  prefetchTransactions(): void {
    const account = this.currentAccountNumber();
    if (!account) return;

    const sortConfig = {property: 'booking_date' as TransactionSortProperty, order: 'desc' as SortOrder};

    this.queryClient.prefetchQuery({
      queryKey: ['transactions', account, 0, 20, sortConfig, undefined],
      queryFn: async () => {
        const request: PageTransactionsRequest = {
          page: 0,
          size: 20,
          sortOrder: sortConfig.order,
          sortProperty: sortConfig.property,
          query: {accountNumber: account}
        };

        const result = await firstValueFrom(
          this.apiService.transactions.pageTransactionsApiTransactionsPagePost(request)
        );

        return {
          ...result,
          content: this.appService.mapTransactionsWithCategory(result.content)
        };
      },
    });
  }

  // ── /budget ───────────────────────────────────────────────────────────
  prefetchBudget(): void {
    const account = this.appService.selectedBankAccount$.getValue();
    if (!account?.accountNumber) return;

    this.queryClient.prefetchQuery({
      queryKey: ['budget', account.accountNumber],
      queryFn: async () => {
        const body: BudgetTreeCreate = {bankAccountId: account.accountNumber};
        return firstValueFrom(
          this.apiService.budget.findOrCreateBudgetApiBudgetFindOrCreatePost(body)
        );
      },
    });
  }

  // ── /categorieën ──────────────────────────────────────────────────────
  prefetchManualReview(): void {
    const account = this.currentAccountNumber();
    if (!account) return;

    this.queryClient.prefetchQuery({
      queryKey: ['manualReviewTransactions', account, TransactionTypeEnum.EXPENSES, 0, 50],
      queryFn: async () => {
        const request: PageUncategorizedTransactionsRequest = {
          page: 0,
          size: 50,
          sortOrder: 'asc' as SortOrder,
          sortProperty: 'counterparty' as TransactionSortProperty,
          bankAccount: account,
          transactionType: TransactionTypeEnum.EXPENSES
        };

        return firstValueFrom(
          this.apiService.transactions
            .pageUncategorizedTransactionsApiTransactionsPageUncategorizedPost(request)
        );
      },
    });
  }

  // ── /regels ───────────────────────────────────────────────────────────
  prefetchRules(): void {
    this.queryClient.prefetchQuery({
      queryKey: ['allRuleSetWrappers'],
      queryFn: () => firstValueFrom(this.rulesService.getOrCreateAllRuleSetWrappers()),
    });
  }

  // ── helpers ───────────────────────────────────────────────────────────
  private currentAccountNumber(): string | undefined {
    return this.appService.selectedBankAccount$.getValue()?.accountNumber;
  }
}
