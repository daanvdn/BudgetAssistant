import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ExpensesRevenueToggleComponent } from './expenses-revenue-toggle.component';

describe('ExpensesRevenueToggleComponent', () => {
  let component: ExpensesRevenueToggleComponent;
  let fixture: ComponentFixture<ExpensesRevenueToggleComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ExpensesRevenueToggleComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ExpensesRevenueToggleComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
