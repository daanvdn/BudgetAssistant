/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DebugElement } from '@angular/core';

import { Transactions0Component } from './transactions0.component';

describe('Transactions0Component', () => {
  let component: Transactions0Component;
  let fixture: ComponentFixture<Transactions0Component>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
    imports: [Transactions0Component]
})
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(Transactions0Component);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
