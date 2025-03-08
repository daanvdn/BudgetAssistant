/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DebugElement } from '@angular/core';

import { BooleanRadioButtonGroupComponent } from './boolean-radio-button-group.component';

describe('BooleanRadioButtonGroupComponent', () => {
  let component: BooleanRadioButtonGroupComponent;
  let fixture: ComponentFixture<BooleanRadioButtonGroupComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
    imports: [BooleanRadioButtonGroupComponent]
})
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(BooleanRadioButtonGroupComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
