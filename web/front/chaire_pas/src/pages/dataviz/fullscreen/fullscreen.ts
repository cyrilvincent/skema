import { Component, signal } from '@angular/core';
import { GeoInputDTO } from '../dataviz.interfaces';
import { GeoDataviz } from '../geo-dataviz/geo-dataviz';

@Component({
  selector: 'app-fullscreen',
  imports: [GeoDataviz],
  templateUrl: './fullscreen.html',
  styleUrl: './fullscreen.scss',
})
export class Fullscreen {

  dto = signal<GeoInputDTO | null>(null);
  type = signal<string>("APL");

  constructor() {
    const usp = new URLSearchParams(window.location.search);
    const dto: GeoInputDTO = {
      code: usp.get("code")!,
      id:  Number(usp.get("specialite")!), 
      bor: "", 
      time: Number(usp.get("time")!),
      exp: Number(usp.get("exp")!),
      hc: usp.get("hc")!,
      resolution: usp.get("resolution")!,
    };
    this.dto.set(dto);
    this.type.set(usp.get("type")!)
    console.log("DTO "+this.type());
    console.log(this.dto());
    }

}
