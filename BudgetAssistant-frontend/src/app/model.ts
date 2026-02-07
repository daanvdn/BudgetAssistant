import {CategoryRead, TransactionTypeEnum, TransactionRead} from '@daanvdn/budget-assistant-client';

// Define local types that were previously imported from the client
export interface SimpleCategory {
    id: number;
    name: string;
    qualifiedName: string;
}

export interface SimplifiedCategory {
    id: number;
    name: string;
    qualifiedName: string;
    type: string;
    children?: any[];
}

export type TypeEnum = 'EXPENSES' | 'REVENUE';

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
    withoutCategoryCount: number
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

// CategoryNode has been replaced by SimplifiedCategory

export function inferAmountType(amount: number) {
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
    nodeId!: number;
    type!: TypeEnum;
}


// Type that can be either SimplifiedCategory or CategoryRead
export type CategoryNode = SimplifiedCategory | CategoryRead;

export class CategoryMap {

    private idToNameMap: Map<number, string> = new Map<number, string>();
    private qualifiedNameToIdMap: Map<string, number> = new Map<string, number>();
    private qualifiedNameToNameMap: Map<string, string> = new Map<string, string>();
    private simpleCategoryMap: Map<string, SimpleCategory> = new Map<string, SimpleCategory>();

    constructor(nodes: CategoryNode[]) {
        for (let node of nodes) {
            this.populateMaps(node);
        }
    }

    private populateMaps(node: CategoryNode) {
        // Support both SimplifiedCategory (with .id) and CategoryRead (with .id)
        const nodeId = 'id' in node ? node.id : -1;
        this.idToNameMap.set(nodeId, node.name);
        this.qualifiedNameToIdMap.set(node.qualifiedName, nodeId);
        this.qualifiedNameToNameMap.set(node.qualifiedName, node.name);

        // Store a SimpleCategory object for each node
        this.simpleCategoryMap.set(node.qualifiedName, {
            qualifiedName: node.qualifiedName,
            name: node.name,
            id: nodeId
        });

        // Process children - handle both SimplifiedCategory and CategoryRead structures
        if (node.children && node.children.length > 0) {
            for (let childObj of node.children) {
                // For CategoryRead, children is Array<CategoryRead>
                if ('qualifiedName' in childObj) {
                    this.populateMaps(childObj as CategoryRead);
                } else {
                    // For SimplifiedCategory, children have a different structure
                    const entries = Object.entries(childObj);
                    if (entries.length > 0) {
                        const [_, value] = entries[0];
                        const childCategory = value as unknown as SimplifiedCategory;
                        this.populateMaps(childCategory);
                    }
                }
            }
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

    public getSimpleCategory(qualifiedName: string): SimpleCategory | null {
        // If qualifiedName is undefined or null, return null
        if (!qualifiedName) {
            return null;
        }

        let simpleCategory = this.simpleCategoryMap.get(qualifiedName);
        if (simpleCategory === undefined) {
            // If the category doesn't exist in our map, create a default one
            // This handles cases where the category might be from an external source
            // or was added after the CategoryMap was initialized
            console.warn("No SimpleCategory found for qualified name " + qualifiedName + ". Creating a default one.");
            return {
                qualifiedName: qualifiedName,
                name: qualifiedName.split('.').pop() || qualifiedName, // Use the last part of the qualified name as the name
                id: -1 // Use a default ID
            };
        }
        return simpleCategory;
    }

}

export interface TransactionWithCategory extends TransactionRead {
    category?: CategoryRead;
}

/**
 * Given a TransactionRead and a category index (id->CategoryRead),
 * returns a TransactionWithCategory with the resolved category property.
 */
export function resolveTransactionCategory(
    transaction: TransactionRead,
    categoryIndex: { [id: number]: CategoryRead }
): TransactionWithCategory {
    return {
        ...transaction,
        category: transaction.categoryId != null ? categoryIndex[transaction.categoryId] : undefined,
    };
}
