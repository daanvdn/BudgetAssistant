import {
    BankAccountRead,
    CategoryRead,
    Grouping,
    TransactionRead,
    TransactionTypeEnum
} from '@daanvdn/budget-assistant-client';

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


export interface FileWrapper {

    file: File;
    inProgress: Boolean;
    progress: Number;
    failed: Boolean;

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

export class Criteria {
    bankAccount: BankAccountRead;
    grouping: Grouping;
    startDate: Date;
    endDate: Date;
    transactionType: TransactionTypeEnum | undefined;

    constructor(bankAccount: BankAccountRead, grouping: Grouping, startDate: Date, endDate: Date,
                transactionType: TransactionTypeEnum | undefined) {
        this.bankAccount = bankAccount;
        this.grouping = grouping;
        this.startDate = startDate;
        this.endDate = endDate;
        this.transactionType = transactionType;
    }

    public equals(criteria: Criteria): boolean {
        if (!criteria || !criteria.bankAccount || !criteria.grouping || !criteria.startDate || !criteria.endDate) {
            return false;
        }
        if (this.transactionType !== criteria.transactionType) {
            return false;
        }
        return this.bankAccount.accountNumber === criteria.bankAccount.accountNumber &&
            this.grouping === criteria.grouping &&
            this.startDate === criteria.startDate &&
            this.endDate === criteria.endDate &&
            this.transactionType === criteria.transactionType;
    }
}