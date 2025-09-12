import {Component, EventEmitter, OnInit, Output, ViewChild} from '@angular/core';
import {FormBuilder, FormsModule} from '@angular/forms';
import {NgSelectComponent} from '@ng-select/ng-select';
import {Observable, of} from 'rxjs';
import {MatFormField, MatLabel} from '@angular/material/form-field';
import {MatInput} from '@angular/material/input';
import {NgForOf} from '@angular/common';
import {TransactionTypeEnum} from "@daanvdn/budget-assistant-client";
import {MatOption, MatSelect} from "@angular/material/select";


export interface TransactionTypeSelection {
    minAmount?: number;
    maxAmount?: number;
    transactionType?: TransactionTypeEnum;
}

@Component({
    selector: 'app-transactiontype-selection',
    templateUrl: './transactiontype-selection.component.html',
    styleUrls: ['./transactiontype-selection.component.scss'],
    standalone: true,
    imports: [MatFormField, MatLabel, MatInput, FormsModule, MatSelect, MatOption, NgForOf]
})


export class TransactiontypeSelectionComponent implements OnInit {


    transactionTypes: Map<string, TransactionTypeEnum> = new Map<string, TransactionTypeEnum>();
    transactionTypesObservable!: Observable<string[]>;
    selectedTransactionType!: TransactionTypeEnum;
    minAmount!: number;
    maxAmount!: number;
    @ViewChild(NgSelectComponent) ngSelect!: NgSelectComponent;
    transactionTypeKeys: string[] = [];



    @Output() transactionTypeChange: EventEmitter<TransactionTypeSelection> = new EventEmitter<TransactionTypeSelection>();

    constructor(private formBuilder: FormBuilder) {
        this.transactionTypes.set("in- & uitkomsten", TransactionTypeEnum.BOTH)
        this.transactionTypes.set("uitgaven", TransactionTypeEnum.EXPENSES)
        this.transactionTypes.set("inkomsten", TransactionTypeEnum.REVENUE)
        this.transactionTypesObservable = of(Array.from(this.transactionTypes.keys()))
        this.transactionTypeKeys = Array.from(this.transactionTypes.keys());

    }

    ngOnInit() {

    }

    public onSelectionChange(): void {
        let sel = this.getSelectedTransactionType();
        if (sel !== null && sel != undefined) {
            this.selectedTransactionType = sel;
            this.transactionTypeChange.emit();
        }
    }

    /**
     * we cannot use two-way binding on ngModel because of how ng-select works. so this is a workaround
     * @returns
     */

    private getSelectedTransactionType(): TransactionTypeEnum | null | undefined {
        let selectedItems = this.ngSelect.selectedItems;
        if (selectedItems == null || selectedItems.length === 0) {
            return null;
        }
        if (selectedItems.length != 1) {
            throw new Error("only 1 item can be selected!")
        }
        let firstValue: string | undefined = selectedItems[0].value;
        if (firstValue === undefined) {
            throw new Error("value must not be undefined!")
        }

        return this.transactionTypes.get(firstValue);


    }


    onTransactionTypeChange() {
        this.transactionTypeChange.emit({
            minAmount: this.minAmount,
            maxAmount: this.maxAmount,
            transactionType: this.selectedTransactionType
        });
    }

    onMinAmountChange() {
        this.transactionTypeChange.emit({
            minAmount: this.minAmount,
            maxAmount: this.maxAmount,
            transactionType: this.selectedTransactionType
        });
    }
    onMaxAmountChange() {
        this.transactionTypeChange.emit({
            minAmount: this.minAmount,
            maxAmount: this.maxAmount,
            transactionType: this.selectedTransactionType
        });
    }
}
