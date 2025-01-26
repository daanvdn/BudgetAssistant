/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DebugElement } from '@angular/core';

import { RevenueExpensesPerPeriodAndCategoryComponent } from './revenue-expenses-per-period-and-category.component';

describe('InkomstenUitgavenPerCategoryComponent', () => {
  let component: RevenueExpensesPerPeriodAndCategoryComponent;
  let fixture: ComponentFixture<RevenueExpensesPerPeriodAndCategoryComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ RevenueExpensesPerPeriodAndCategoryComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(RevenueExpensesPerPeriodAndCategoryComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
