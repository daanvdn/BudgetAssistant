import { TestBed } from '@angular/core/testing';

import { CategoryRulesService } from './category-rules.service';

describe('CategoryRulesService', () => {
  let service: CategoryRulesService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(CategoryRulesService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
