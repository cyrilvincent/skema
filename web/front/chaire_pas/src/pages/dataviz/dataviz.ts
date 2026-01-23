import { Component, signal } from '@angular/core';
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
})
export class Dataviz {
  selectedCode = signal<string | null>(null);
  specialite = signal<GeoInputDTO | null>(null);
  dto = signal<GeoInputDTO | null>(null);

  optionSelected(code: string | null) {
    this.selectedCode.set(code);
  }

  ok(params: [Specialite, number, number, string, boolean]): void {
    const s: GeoInputDTO = {
      code: this.selectedCode() ?? "38205", // TODO
      id: params[0].id, 
      bor: params[0].shortLabel, 
      time: params[1],
      exp: params[2],
      hc: params[3]
    };
    this.dto.set(s);
  }

}
