import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CriteriaToolbarComponent } from './criteria-toolbar.component';

describe('CriteriaToolbarComponent', () => {
  let component: CriteriaToolbarComponent;
  let fixture: ComponentFixture<CriteriaToolbarComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ CriteriaToolbarComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CriteriaToolbarComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
