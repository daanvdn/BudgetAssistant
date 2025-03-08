/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DebugElement } from '@angular/core';

import { CounterpartyAccountNumberSelectionComponent } from './counterparty-account-number-selection.component';

describe('TegenpartijRekeningSelectionComponent', () => {
  let component: CounterpartyAccountNumberSelectionComponent;
  let fixture: ComponentFixture<CounterpartyAccountNumberSelectionComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
    imports: [CounterpartyAccountNumberSelectionComponent]
})
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(CounterpartyAccountNumberSelectionComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
