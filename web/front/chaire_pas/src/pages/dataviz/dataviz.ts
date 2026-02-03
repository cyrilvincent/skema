import { ChangeDetectionStrategy, Component, input, signal } from '@angular/core';
import { Searchbox } from './searchbox/searchbox';
import { DatavizParameters } from "./dataviz-parameters/dataviz-parameters";
import {MatDividerModule} from '@angular/material/divider';
import { GeoDataviz } from "./geo-dataviz/geo-dataviz";
import { Specialite, GeoInputDTO } from './dataviz.interfaces';

@Component({
  selector: 'app-dataviz',
  imports: [Searchbox, DatavizParameters, MatDividerModule, GeoDataviz],
  templateUrl: './dataviz.html',
  styleUrl: './dataviz.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Dataviz {
  selectedCode = signal<string | null>(null);
  specialite = signal<GeoInputDTO | null>(null);
  dto = signal<GeoInputDTO | null>(null);
  type = input<string>("APL");
  geoType = signal<string>("iris");

  optionSelected(code: string | null) {
    this.selectedCode.set(code);
  }

  ok(params: [Specialite, number, number, string, boolean, string, string]): void {
    const s: GeoInputDTO = {
      code: this.selectedCode() ?? "CC-38205",
      id: params[0].id, 
      bor: params[0].shortLabel, 
      time: params[1],
      exp: params[2],
      hc: params[3],
      resolution: params[5],
    };
    this.dto.set(s);
    this.geoType.set(params[6])
    console.log("OK");
    console.log(this.dto());
  }

}
