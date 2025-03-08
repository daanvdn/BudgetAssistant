/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DebugElement } from '@angular/core';

import { CategoryTreeDropdownComponent } from './category-tree-dropdown.component';

describe('CategoryTreeComponent', () => {
  let component: CategoryTreeDropdownComponent;
  let fixture: ComponentFixture<CategoryTreeDropdownComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
    imports: [CategoryTreeDropdownComponent]
})
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(CategoryTreeDropdownComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
