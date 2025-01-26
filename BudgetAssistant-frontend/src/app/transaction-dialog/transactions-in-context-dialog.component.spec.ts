import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TransactionsInContextDialogComponent } from './transactions-in-context-dialog.component';

describe('TransactionDialogComponent', () => {
  let component: TransactionsInContextDialogComponent;
  let fixture: ComponentFixture<TransactionsInContextDialogComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ TransactionsInContextDialogComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(TransactionsInContextDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
