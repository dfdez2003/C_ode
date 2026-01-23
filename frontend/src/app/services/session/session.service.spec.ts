// frontend/src/app/services/session/session.service.spec.ts

import { TestBed } from '@angular/core/testing';
import { SessionService } from './session.service';
import { HttpClientTestingModule } from '@angular/common/http/testing';

describe('SessionService', () => {
  let service: SessionService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [SessionService]
    });
    service = TestBed.inject(SessionService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should initialize with no active session', () => {
    expect(service.currentSessionId()).toBeNull();
    expect(service.isSessionActive()).toBeFalsy();
  });

  it('should format duration correctly', () => {
    const formatted = service.getFormattedDuration();
    expect(formatted).toMatch(/\d{2}:\d{2}:\d{2}/);
  });
});
