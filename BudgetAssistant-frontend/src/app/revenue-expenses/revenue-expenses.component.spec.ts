/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DebugElement } from '@angular/core';

import { ExpensesRevenueComponent } from './revenue-expenses.component';

describe('InkomstenUitgavenPerJaarComponent', () => {
  let component: ExpensesRevenueComponent;
  let fixture: ComponentFixture<ExpensesRevenueComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
    imports: [ExpensesRevenueComponent]
})
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ExpensesRevenueComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
