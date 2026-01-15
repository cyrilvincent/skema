import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Observatoire } from './observatoire';

describe('Observatoire', () => {
  let component: Observatoire;
  let fixture: ComponentFixture<Observatoire>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Observatoire]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Observatoire);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
