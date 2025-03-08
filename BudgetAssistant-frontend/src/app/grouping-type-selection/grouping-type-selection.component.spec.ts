/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DebugElement } from '@angular/core';

import { GroupingTypeSelectionComponent } from './grouping-type-selection.component';

describe('GroupingTypeSelectionComponent', () => {
  let component: GroupingTypeSelectionComponent;
  let fixture: ComponentFixture<GroupingTypeSelectionComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
    imports: [GroupingTypeSelectionComponent]
})
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(GroupingTypeSelectionComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
