/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DebugElement } from '@angular/core';

import { RecurrenceComponent } from './recurrence.component';

describe('UitgavenTypeComponent', () => {
  let component: RecurrenceComponent;
  let fixture: ComponentFixture<RecurrenceComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
    imports: [RecurrenceComponent]
})
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(RecurrenceComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
