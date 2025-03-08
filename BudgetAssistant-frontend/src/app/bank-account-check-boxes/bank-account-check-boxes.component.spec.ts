import { ComponentFixture, TestBed } from '@angular/core/testing';

import { BankAccountCheckBoxesComponent } from './bank-account-check-boxes.component';

describe('BankAccountCheckBoxesComponent', () => {
  let component: BankAccountCheckBoxesComponent;
  let fixture: ComponentFixture<BankAccountCheckBoxesComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
    imports: [BankAccountCheckBoxesComponent]
})
    .compileComponents();

    fixture = TestBed.createComponent(BankAccountCheckBoxesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
