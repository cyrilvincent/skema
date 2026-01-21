import { ComponentFixture, TestBed } from '@angular/core/testing';

import { GeoDataviz } from './geo-dataviz';

describe('GeoDataviz', () => {
  let component: GeoDataviz;
  let fixture: ComponentFixture<GeoDataviz>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [GeoDataviz]
    })
    .compileComponents();

    fixture = TestBed.createComponent(GeoDataviz);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
