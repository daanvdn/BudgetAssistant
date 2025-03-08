/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DebugElement } from '@angular/core';

import { BankAccountSelectionComponent } from './bank-account-selection.component';

describe('RekeningSelectionComponent', () => {
  let component: BankAccountSelectionComponent;
  let fixture: ComponentFixture<BankAccountSelectionComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
    imports: [BankAccountSelectionComponent]
})
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(BankAccountSelectionComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
