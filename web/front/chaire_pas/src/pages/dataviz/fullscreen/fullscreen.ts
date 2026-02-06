import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { GeoInputDTO } from '../dataviz.interfaces';
import { GeoDataviz } from '../geo-dataviz/geo-dataviz';
import {MatProgressSpinnerModule} from '@angular/material/progress-spinner';
import { GeoService } from '../geo-dataviz/geo-service';

@Component({
  selector: 'app-fullscreen',
  imports: [GeoDataviz, MatProgressSpinnerModule],
  templateUrl: './fullscreen.html',
  styleUrl: './fullscreen.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Fullscreen {

  dto = signal<GeoInputDTO | null>(null);
  type = signal<string>("APL");
  service = inject(GeoService);
  label = signal<string>("");

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
    this.label.set(usp.get("label")!)
    console.log("DTO "+this.type());
    console.log(this.dto());
    }

}
