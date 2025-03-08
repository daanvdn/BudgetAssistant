/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DebugElement } from '@angular/core';

import { PeriodSelectionComponent } from './period-selection.component';

describe('PeriodSelectionComponent', () => {
  let component: PeriodSelectionComponent;
  let fixture: ComponentFixture<PeriodSelectionComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
    imports: [PeriodSelectionComponent]
})
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PeriodSelectionComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
