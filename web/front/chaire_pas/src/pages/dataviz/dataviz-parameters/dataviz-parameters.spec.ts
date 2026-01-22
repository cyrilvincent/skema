import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DatavizParameters } from './dataviz-parameters';

describe('DatavizParameters', () => {
  let component: DatavizParameters;
  let fixture: ComponentFixture<DatavizParameters>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DatavizParameters]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DatavizParameters);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
