import { ComponentFixture, TestBed } from '@angular/core/testing';

import { RulesBuilderComponent } from './rules-builder.component';

describe('CategoryRulesComponent', () => {
  let component: RulesBuilderComponent;
  let fixture: ComponentFixture<RulesBuilderComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ RulesBuilderComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(RulesBuilderComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
