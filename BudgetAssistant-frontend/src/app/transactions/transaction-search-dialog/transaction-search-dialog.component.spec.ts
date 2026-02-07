/* tslint:disable:no-unused-variable */
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { HttpClientTestingModule } from '@angular/common/http/testing';

import { TransactionSearchDialogComponent } from './transaction-search-dialog.component';
import { AppService } from '../../app.service';
import { BehaviorSubject } from 'rxjs';

describe('TransactionSearchDialogComponent', () => {
  let component: TransactionSearchDialogComponent;
  let fixture: ComponentFixture<TransactionSearchDialogComponent>;

  const mockAppService = {
    categoryIndexObservable$: new BehaviorSubject(undefined),
    selectedBankAccountObservable$: new BehaviorSubject(undefined),
    getDistinctCounterpartyNames: () => new BehaviorSubject([]),
    getDistinctCounterpartyAccounts: () => new BehaviorSubject([]),
    resolveStartEndDateShortcut: () => new BehaviorSubject({ start: new Date(), end: new Date() })
  };

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      imports: [
        TransactionSearchDialogComponent,
        NoopAnimationsModule,
        HttpClientTestingModule
      ],
      providers: [
        { provide: MatDialogRef, useValue: { close: () => {} } },
        { provide: MAT_DIALOG_DATA, useValue: {} },
        { provide: AppService, useValue: mockAppService }
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(TransactionSearchDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should have transaction type options', () => {
    expect(component.transactionTypeOptions.length).toBe(3);
  });

  it('should have period shortcut options', () => {
    expect(component.periodShortcutOptions.length).toBe(7);
  });

  it('should build transaction query on search click', () => {
    const closeSpy = spyOn(component.dialogRef, 'close');
    // Set at least one filter to pass validation
    component.counterpartyNameControl.setValue('Test');
    component.onSearchClick();
    expect(closeSpy).toHaveBeenCalled();
  });

  it('should close dialog on cancel click', () => {
    const closeSpy = spyOn(component.dialogRef, 'close');
    component.onCancelClick();
    expect(closeSpy).toHaveBeenCalledWith();
  });

  it('should show validation error when no filters are set', () => {
    const closeSpy = spyOn(component.dialogRef, 'close');
    component.onSearchClick();
    expect(component.showValidationError).toBe(true);
    expect(closeSpy).not.toHaveBeenCalled();
  });

  it('should not show validation error when a filter is set', () => {
    component.counterpartyNameControl.setValue('Test Counterparty');
    component.onSearchClick();
    expect(component.showValidationError).toBe(false);
  });

  it('should detect transaction type as a valid filter', () => {
    component.transactionTypeControl.setValue('EXPENSES' as any);
    expect(component.hasAnyFilter()).toBe(true);
  });

  it('should detect min amount as a valid filter', () => {
    component.minAmountControl.setValue(100);
    expect(component.hasAnyFilter()).toBe(true);
  });

  it('should detect date range as a valid filter', () => {
    component.range.controls.start.setValue(new Date());
    expect(component.hasAnyFilter()).toBe(true);
  });
});
