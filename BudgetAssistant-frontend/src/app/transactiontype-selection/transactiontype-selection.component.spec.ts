/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DebugElement } from '@angular/core';

import { TransactiontypeSelectionComponent } from './transactiontype-selection.component';

describe('TransactiontypeSelectionComponent', () => {
  let component: TransactiontypeSelectionComponent;
  let fixture: ComponentFixture<TransactiontypeSelectionComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
    imports: [TransactiontypeSelectionComponent]
})
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(TransactiontypeSelectionComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
