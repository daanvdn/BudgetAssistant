import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ManualCategorizationViewComponent } from './manual-categorization-view.component';

describe('ManualCategorizationViewComponent', () => {
  let component: ManualCategorizationViewComponent;
  let fixture: ComponentFixture<ManualCategorizationViewComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
    imports: [ManualCategorizationViewComponent]
})
    .compileComponents();

    fixture = TestBed.createComponent(ManualCategorizationViewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
