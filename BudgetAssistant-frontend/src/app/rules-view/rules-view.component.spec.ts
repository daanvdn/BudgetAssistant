import { ComponentFixture, TestBed } from '@angular/core/testing';

import { RulesViewComponent } from './rules-view.component';

describe('ExpensesRulesViewComponent', () => {
  let component: RulesViewComponent;
  let fixture: ComponentFixture<RulesViewComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
    imports: [RulesViewComponent]
})
    .compileComponents();

    fixture = TestBed.createComponent(RulesViewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
