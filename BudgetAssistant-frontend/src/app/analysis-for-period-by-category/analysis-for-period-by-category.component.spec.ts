import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AnalysisForPeriodByCategoryComponent } from './analysis-for-period-by-category.component';

describe('AnalysisForPeriodByCategoryComponent', () => {
  let component: AnalysisForPeriodByCategoryComponent;
  let fixture: ComponentFixture<AnalysisForPeriodByCategoryComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
    imports: [AnalysisForPeriodByCategoryComponent]
})
    .compileComponents();

    fixture = TestBed.createComponent(AnalysisForPeriodByCategoryComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
