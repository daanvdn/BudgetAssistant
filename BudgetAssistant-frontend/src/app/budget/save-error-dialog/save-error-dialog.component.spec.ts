import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SaveErrorDialogComponent } from './save-error-dialog.component';

describe('SaveErrorDialogComponent', () => {
  let component: SaveErrorDialogComponent;
  let fixture: ComponentFixture<SaveErrorDialogComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ SaveErrorDialogComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(SaveErrorDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
