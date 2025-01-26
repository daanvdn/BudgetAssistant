import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CategorizationComponent } from './categorization.component';

describe('CategorizationComponent', () => {
  let component: CategorizationComponent;
  let fixture: ComponentFixture<CategorizationComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ CategorizationComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CategorizationComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
