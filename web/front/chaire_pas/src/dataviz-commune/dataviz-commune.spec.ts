import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DatavizCommune } from './dataviz-commune';

describe('DatavizCommune', () => {
  let component: DatavizCommune;
  let fixture: ComponentFixture<DatavizCommune>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DatavizCommune]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DatavizCommune);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
