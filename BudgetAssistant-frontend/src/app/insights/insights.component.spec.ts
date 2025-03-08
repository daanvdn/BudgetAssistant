/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DebugElement } from '@angular/core';

import { InsightsComponent } from './insights.component';

describe('AnalysisComponent', () => {
  let component: InsightsComponent;
  let fixture: ComponentFixture<InsightsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
    imports: [InsightsComponent]
})
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(InsightsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
