export interface CategoryAndAmount {
    amount: number;
    category: string;
    categoryId: number;
    isRevenue: boolean;

}

export function anyIsUndefinedOrEmpty(...args: any[]): boolean {
    for (var a of args) {
        if (a === undefined || a === null) {
            return true;
        }
        //check if string
        if (typeof a === 'string' && a === "") {
            return true;
        }


    }

    return false;

}

export interface PeriodAndAmount {

    period: string;
    amount: Number;

}

export interface Counterparty {

    name: string;
    accountNumber: string | null;
    streetAndNumber: string | null;
    zipCodeAndCity: string | null;
    category: string | null;

}

export interface Transaction {

    transaction_id: string | null;
    bankAccount: string | null;
    bookingDate: Date | null;
    statementNumber: string | null;
    transactionNumber: number | null;
    counterparty: Counterparty | null;
    transaction: string | null;
    currencyDate: Date | null;
    amount: Number | null;
    currency: string | null;
    bic: string | null;
    countryCode: string | null;
    communications: string | null;
    category: string | null;
    manuallyAssignedCategory: Boolean | null;
    isRecurring: Boolean | null;
    isAdvanceSharedAccount: Boolean | null;
    isManuallyReviewed: Boolean | null;


}


export interface TransactionQuery {


    revenue: Boolean | undefined;
    expenses: Boolean | undefined;
    counterpartyName: string | undefined;
    minAmount: Number | undefined;
    maxAmount: Number | undefined;
    accountNumber: string | undefined;
    category: string | undefined;
    freeText: string | undefined;
    counterpartyAccountNumber: string | undefined;
    startDate: Date | undefined | null;
    endDate: Date | undefined | null;
    transactionOrCommunication: string | undefined | null;
    uploadTimestamp: string | undefined | null;


}

export interface TransactionsInContextQuery{
    bankAccount: string;
    period: string;
    transactionType: TransactionType;
    category: string;
}


export interface FileWrapper {

    file: File;
    inProgress: Boolean;
    progress: Number;
    failed: Boolean;

}


export interface CompositeTransactionsFileUploadResponse {

    responses: TransactionsFileUploadResponse[];
    uploadTimestamp: string;
}

export interface TransactionsFileUploadResponse {

    message: string;
    type: string;

}


export interface TransactionsFileUploadResponseWrapper {
    response: TransactionsFileUploadResponse;
    fileWrapper: FileWrapper;
}


export const EMPTY_TRANSACTION_QUERY: TransactionQuery = {
    revenue: undefined,
    expenses: undefined,
    counterpartyName: undefined,
    minAmount: undefined,
    maxAmount: undefined,
    accountNumber: undefined,
    category: undefined,
    freeText: undefined,
    counterpartyAccountNumber: undefined,
    startDate: undefined,
    endDate: undefined,
    transactionOrCommunication: undefined,
    uploadTimestamp: undefined


}


export enum Grouping {
    MONTH = "month",
    QUARTER = "quarter",
    YEAR = "year"


}

export interface DistributionByTransactionTypeForPeriod {
    period: Period;
    revenue: number;
    expenses: number;
    balance: number;
    start: string;
    end: string;

}


export interface DistributionByCategoryForPeriodHandlerResult {
    chartData: DistributionByCategoryForPeriodChartData[];
    tableData: DistributionByCategoryForPeriodTableData[];
    tableColumnNames: string[];
}

export interface DistributionByCategoryForPeriodHandlerResult2 {
    chartDataRevenue: DistributionByCategoryForPeriodChartData[];
    chartDataExpenses: DistributionByCategoryForPeriodChartData[];
    tableDataRevenue: DistributionByCategoryForPeriodTableData[]
    tableDataExpenses: DistributionByCategoryForPeriodTableData[]
    tableColumnNames: string[];
}


export interface Dataset {
    label: string;
    data: number[];
    maxBarThickness?: number;
}

export interface CategoryDetailsForPeriodHandlerResult {
    labels: string[];
    datasets: Dataset[];
}


export interface Period {

    start: string;
    end: string;
    grouping: Grouping;
    value: string;


}


export const EMPTY_PERIOD: Period = {
    start: "",
    end: "",
    grouping: Grouping.MONTH,
    value: ""

}

export enum TransactionType {
    REVENUE = "revenue",
    EXPENSES = "expenses",
    BOTH = "both"


}

export interface DistributionByCategoryForPeriodChartData {
    period: object;
    transactionType: TransactionType;
    entries: CategoryAndAmount[];

}


export interface DistributionByCategoryForPeriodTableData {
    [key: string]: any;

}

export interface RevenueExpensesQuery {

    accountNumber: string | null | undefined;
    grouping: Grouping | null | undefined;
    transactionType: TransactionType | null | undefined;
    start: Date | null | undefined;
    end: Date | null | undefined;
    revenueRecurrence: string | null | undefined;
    expensesRecurrence: string | null | undefined;


}

export const EMPTY_REVENUE_EXPENSES_QUERY: RevenueExpensesQuery = {
    accountNumber: undefined,
    grouping: undefined,
    transactionType: undefined,
    start: undefined,
    end: undefined,
    revenueRecurrence: undefined,
    expensesRecurrence: undefined
}

export class ResolvedStartEndDateShortcut {
    start: Date;
    end: Date;

    constructor(start: Date, end: Date) {
        this.start = start
        this.end = end
    }


}

export enum StartEndDateShortcut {


    CURRENT_MONTH = "current month",
    PREVIOUS_MONTH = "previous month",
    CURRENT_QUARTER = "current quarter",
    PREVIOUS_QUARTER = "previous quarter",
    CURRENT_YEAR = "current year",
    PREVIOUS_YEAR = "previous year",
    ALL = "all"
}

export interface User {
    firstName: string | undefined
    lastName: string | undefined
    userName: string | undefined;
    password: string | undefined;
    email: string | undefined;
    bankAccounts: string[] | undefined;
}

export const DUMMY_USER: User = {
    firstName: undefined,
    lastName: undefined,
    email: undefined,
    password: undefined,
    bankAccounts: undefined,
    userName: undefined
}

export enum Type {
    SUCCESS = "SUCCESS", FAILED = "FAILED"
}

export interface TransactionsCategorizationResponse {
    message: string;
    withCategoryCount: number;
    withoutCategoryCount: number;
    type: Type;
}

export interface BankAccount {

    accountNumber: string;
    alias: string | undefined | null;
    editAlias: boolean;

}

export enum ActiveView {
    EXPENSES = "expenses", REVENUE = "revenue"
}


interface BudgetTrackerResultNode {
    data: Record<string, any>;
    children: BudgetTrackerResultNode[];
    leaf: boolean;
}

export interface BudgetTrackerResult {

    data: BudgetTrackerResultNode[];
    columns: string[];


}


export type CategoryType = "EXPENSES" | "REVENUE";

export interface CategoryNode {

    children: CategoryNode[];
    name: string;
    qualifiedName: string;
    type: CategoryType | undefined;
    id: number;


}

export function inferAmountType(amount: Number) {
    if (amount >= 0) {
        return AmountType.REVENUE;
    }
    else if (amount < 0) {
        return AmountType.EXPENSES;
    }
    else {
        throw new Error("Unknown amount type " + amount);
    }
}

export enum AmountType {
    REVENUE = "REVENUE",
    EXPENSES = "EXPENSES",
    BOTH = "BOTH",
}

export class FlatCategoryNode {
    level!: number;
    expandable!: boolean;
    name!: string;
    qualifiedName!: string;
    type: CategoryType | undefined;
}

const DUMMY_CATEGORY: CategoryNode = {
    children: [],
    name: "DUMMY CATEGORY",
    qualifiedName: "DUMMY CATEGORY",
    type: undefined,
    id: -1
}
export const NO_CATEGORY: CategoryNode = {
    children: [],
    name: "NO CATEGORY",
    qualifiedName: "NO CATEGORY",
    type: undefined ,
    id: -1
}

export class CategoryMap {

    private idToNameMap: Map<number, string> = new Map<number, string>();
    private qualifiedNameToIdMap: Map<string, number> = new Map<string, number>();
    private qualifiedNameToNameMap: Map<string, string> = new Map<string, string>();

    constructor(nodes: CategoryNode[]) {
        for (let node of nodes) {
            this.populateMaps(node);
        }
    }

    private populateMaps(node: CategoryNode) {
        this.idToNameMap.set(node.id, node.name);
        this.qualifiedNameToIdMap.set(node.qualifiedName, node.id);
        this.qualifiedNameToNameMap.set(node.qualifiedName, node.name);
        for (let child of node.children) {
            this.populateMaps(child);
        }
    }

    public getName(id: number): string {
        let name = this.idToNameMap.get(id);
        if (name === undefined) {
            throw new Error("No name found for id " + id);
        }
        return name;
    }

    public getId(qualifiedName: string): number {
        let id = this.qualifiedNameToIdMap.get(qualifiedName);
        if (id === undefined) {
            throw new Error("No id found for qualified name " + qualifiedName);
        }
        return id;
    }


}