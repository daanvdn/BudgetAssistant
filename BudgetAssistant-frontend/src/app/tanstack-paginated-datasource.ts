// Generic Tanstack Query-based DataSource for Angular Material Table with pagination
import {DataSource, CollectionViewer} from '@angular/cdk/collections';
import {injectQuery} from '@tanstack/angular-query-experimental';
import {signal, effect} from '@angular/core';
import {BehaviorSubject, Observable, firstValueFrom} from 'rxjs';
import {Page} from 'ngx-pagination-data-source';
import {MatPaginator} from '@angular/material/paginator';
import {MatSort, SortDirection} from '@angular/material/sort';

export interface Sort { property: string; direction: SortDirection; }

export class TanstackPaginatedDataSource<T, Q> implements DataSource<T> {

  private dataSubject = new BehaviorSubject<T[]>([]);
  readonly totalElements = signal(0);
  readonly isLoading = signal(false);

  private pageSignal = signal<{ pageIndex: number; pageSize: number }>({ pageIndex: 0, pageSize: 10 });
  private sortSignal = signal<Sort>({ property: '', direction: 'asc' });
  private querySignal = signal<Q>(undefined as unknown as Q);

  constructor(
    private queryKey: unknown[],
    private fetchPageFn: (params: { page: number; size: number; sort: Sort; query: Q }) => Promise<Page<T>> | Observable<Page<T>>,
    initialQuery: Q,
    initialSort?: Sort
  ) {
    // initialize signals
    this.querySignal.set(initialQuery);
    if (initialSort) {
      this.sortSignal.set(initialSort);
    }

    const q = injectQuery<Page<T>>(() => ({
      queryKey: [
        ...this.queryKey,
        this.pageSignal().pageIndex,
        this.pageSignal().pageSize,
        this.sortSignal(),
        this.querySignal()
      ],
      queryFn: async (): Promise<Page<T>> => {
        const result = await this.fetchPageFn({
          page: this.pageSignal().pageIndex,
          size: this.pageSignal().pageSize,
          sort: this.sortSignal(),
          query: this.querySignal()
        });
        if (result instanceof Observable) {
          return firstValueFrom(result as Observable<Page<T>>);
        }
        return result as Page<T>;
      }
    }));

    effect(() => {
      const data = q.data();
      this.isLoading.set(q.isFetching());
      if (data) {
        this.dataSubject.next(data.content);
        this.totalElements.set(data.totalElements);
      }
    });
  }

  connect(_viewer: CollectionViewer): Observable<T[]> {
    return this.dataSubject.asObservable();
  }

  disconnect(_viewer: CollectionViewer): void {
    this.dataSubject.complete();
  }

  // allow external controls to drive pagination/sorting/query
  setPage(pageIndex: number, pageSize: number): void {
    this.pageSignal.set({ pageIndex, pageSize });
  }

  setSort(property: string, direction: SortDirection): void {
    this.sortSignal.set({ property, direction });
  }

  setQuery(query: Q): void {
    this.querySignal.set(query);
  }

  // convenience methods for Angular Material controls
  attachPaginator(paginator: MatPaginator): void {
    paginator.page.subscribe(ev => this.setPage(ev.pageIndex, ev.pageSize));
    // trigger initial
    this.setPage(paginator.pageIndex, paginator.pageSize);
  }

  attachSort(sort: MatSort): void {
    sort.sortChange.subscribe(ev => this.setSort(ev.active, ev.direction as SortDirection));
    // trigger initial
    this.setSort(sort.active, sort.direction as SortDirection);
  }
}
