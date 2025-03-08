/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DebugElement } from '@angular/core';

import { TransactionSearchDialogComponent } from './transaction-search-dialog.component';

describe('TransactionSearchDialogComponent', () => {
  let component: TransactionSearchDialogComponent;
  let fixture: ComponentFixture<TransactionSearchDialogComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
    imports: [TransactionSearchDialogComponent]
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
});
