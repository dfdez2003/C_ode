import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MakeCode } from './make-code';

describe('MakeCode', () => {
  let component: MakeCode;
  let fixture: ComponentFixture<MakeCode>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MakeCode]
    })
    .compileComponents();

    fixture = TestBed.createComponent(MakeCode);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
