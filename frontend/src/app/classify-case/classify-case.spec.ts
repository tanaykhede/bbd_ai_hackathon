import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ClassifyCase } from './classify-case';

describe('ClassifyCase', () => {
  let component: ClassifyCase;
  let fixture: ComponentFixture<ClassifyCase>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ClassifyCase]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ClassifyCase);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
