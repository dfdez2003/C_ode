// frontend/src/app/services/progress/progress.service.spec.ts

import { TestBed } from '@angular/core/testing';
import { ProgressService } from './progress.service';
import { HttpClientTestingModule } from '@angular/common/http/testing';

describe('ProgressService', () => {
  let service: ProgressService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [ProgressService]
    });
    service = TestBed.inject(ProgressService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should initialize with no submission result', () => {
    expect(service.lastSubmissionResult()).toBeNull();
  });

  it('should not be submitting initially', () => {
    expect(service.isSubmitting()).toBeFalsy();
  });
});
