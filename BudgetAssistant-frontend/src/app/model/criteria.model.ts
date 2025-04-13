import { BankAccount, GroupingEnum, TransactionTypeEnum } from "@daanvdn/budget-assistant-client";

export class Criteria {
    bankAccount: BankAccount;
    grouping: GroupingEnum;
    startDate: Date;
    endDate: Date;
    transactionType: TransactionTypeEnum | undefined;

    constructor(bankAccount: BankAccount, grouping: GroupingEnum, startDate: Date, endDate: Date,
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