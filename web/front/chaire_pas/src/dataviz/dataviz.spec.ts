import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Dataviz } from './dataviz';

describe('Dataviz', () => {
  let component: Dataviz;
  let fixture: ComponentFixture<Dataviz>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Dataviz]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Dataviz);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
