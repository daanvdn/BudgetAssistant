// Generic Tanstack Query-based DataSource for Angular Material Table with pagination
import {CollectionViewer, DataSource} from '@angular/cdk/collections';
import {injectQuery, keepPreviousData} from '@tanstack/angular-query-experimental';
import {effect, signal} from '@angular/core';
import {BehaviorSubject, firstValueFrom, Observable} from 'rxjs';
import {MatPaginator} from '@angular/material/paginator';
import {MatSort} from '@angular/material/sort';
import {SortOrderEnum, SortPropertyEnum} from "@daanvdn/budget-assistant-client";

export interface Sort {
    property: SortPropertyEnum;
    direction: SortOrderEnum;
}

// no longer using ngx-pagination-data-source; define Page locally
export interface Page<T> {
    content: T[];
    totalElements: number;
    size: number;
    number: number;
}

export class TanstackPaginatedDataSource<T, Q> implements DataSource<T> {

    private dataSubject = new BehaviorSubject<T[]>([]);
    readonly totalElements = signal(0);
    readonly isLoading = signal(false);

    private pageSignal = signal<{ pageIndex: number; pageSize: number }>({pageIndex: 0, pageSize: 10});
    private sortSignal = signal<Sort>({property: SortPropertyEnum.booking_date, direction: SortOrderEnum.asc});
    private querySignal = signal<Q>(undefined as unknown as Q);
    private q: any;

    constructor(
        private fetchPageFn: (params: {
            page: number;
            size: number;
            sort: Sort;
            query: Q
        }) => Promise<Page<T>> | Observable<Page<T>>, private staleTime: number = 1000 * 60 * 5, // default to 5 minutes
    ) {
        // signals initialized with default values

        this.q = injectQuery<Page<T>>(() => ({
            queryKey: [
                fetchPageFn.name, // use function name as part of the query key
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
            },
            placeholderData: keepPreviousData,
            staleTime : staleTime
        }));

        effect(() => {
            const data = this.q.data();
            this.isLoading.set(this.q.isFetching());
            if (data) {
                this.dataSubject.next(data.content);
                this.totalElements.set(data.totalElements);
            }
        }, {allowSignalWrites: true}

            );
    }

    /**
     * Update the current query parameters and refetch
     */
    public setQuery(query: Q): void {
        this.querySignal.set(query);
    }

    /**
     * Update the sort and refetch
     */
    public setSort(sort: Sort): void {
        this.sortSignal.set(sort);
    }

    connect(_viewer: CollectionViewer): Observable<T[]> {
        return this.dataSubject.asObservable();
    }

    disconnect(_viewer: CollectionViewer): void {
        this.dataSubject.complete();
    }

    // allow external controls to drive pagination/sorting/query
    setPage(pageIndex: number, pageSize: number): void {
        this.pageSignal.set({pageIndex, pageSize});
    }

    // convenience methods for Angular Material controls
    attachPaginator(paginator: MatPaginator): void {
        paginator.page.subscribe(ev => this.setPage(ev.pageIndex, ev.pageSize));
        // trigger initial
        this.setPage(paginator.pageIndex, paginator.pageSize);
    }

    attachSort(sort: MatSort): void {
        sort.sortChange.subscribe(ev => this.setSort(
            {
                property: ev.active as SortPropertyEnum,
                direction: ev.direction as SortOrderEnum
            }
        ));
        // trigger initial
        this.setSort(
            {
                property: sort.active as SortPropertyEnum,
                direction: sort.direction as SortOrderEnum
            }
        );
    }

    refresh(): void {
        this.q.refetch();
    }

}
