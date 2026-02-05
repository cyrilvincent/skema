import { computed, inject, Injectable, signal } from '@angular/core';
import { CommonService } from '../../../shared/common.service';
import { GeoInputDTO, GeoTupleDTO } from '../dataviz.interfaces';
import { environment } from '../../../environments/environment';
import { emptyGeo } from '../dataviz.data';
import { FileSaverService } from 'ngx-filesaver';

@Injectable({
  providedIn: 'root',
})
export class GeoService  extends CommonService {
  _geoTupleDTO = signal<GeoTupleDTO>(emptyGeo);          
  geoTupleDTO = computed(() => this._geoTupleDTO());
  fileSaver = inject(FileSaverService);

  fetch(dto: GeoInputDTO, type: string, geoType: string): void {
    if (type == "APL") this.fetchAPL(dto, geoType); 
    else this.fetchSAE(dto, geoType);
  }

  save(dto: GeoInputDTO, type: string, render: string, geoType: string) {
    if (type == "APL") {
      if (render == "json") this.saveAPLJSON(dto, geoType);
      else if (render == "csv") this.saveAPLCSV(dto, geoType);
    }
  }

  private fetchAPL(dto: GeoInputDTO, geoType: string): void {
    console.log("FetchAPL "+geoType);
    console.log(dto);
    this.fetchLoading();
    this.http.post<GeoTupleDTO>(`${environment.baseUrl}/apl/${geoType}`, dto).subscribe({    
      next: (res) => { this._geoTupleDTO.set(res); },
      error: (err) => {
        if(err.status == 404) console.log("Not found "+dto.code);
        else this.catchError(err);
        this._geoTupleDTO.set(emptyGeo);
      },
      complete: () => this._loading.set(false),
    });
  }

  private saveAPLJSON(dto: GeoInputDTO, geoType: string): void {
    console.log("saveAPLJSON "+geoType);
    console.log(dto);
    this.fetchLoading();
    this.http.post<GeoTupleDTO>(`${environment.baseUrl}/apl/${geoType}`, dto).subscribe({    
      next: (res) => {
        const blob = new Blob([JSON.stringify(res)], { type: 'application/json' });
        this.fileSaver.save(blob, `apl_${geoType}_${dto.bor}_${dto.id}_${dto.time}_${dto.hc}_${dto.exp}_${dto.resolution}.json`);
      },
      error: (err) => this.catchError(err),
      complete: () => this._loading.set(false),
    });
  }

  private saveAPLCSV(dto: GeoInputDTO, geoType: string): void {
    console.log("saveAPLCSV "+geoType);
    console.log(dto);
    this.fetchLoading();
    this.http.post<string>(`${environment.baseUrl}/apl/${geoType}/csv`, dto).subscribe({    
      next: (res) => {
        const blob = new Blob([res], { type: 'application/json' });
        this.fileSaver.save(blob, `apl_${geoType}_${dto.bor}_${dto.id}_${dto.time}_${dto.hc}_${dto.exp}.csv`);
      },
      error: (err) => this.catchError(err),
      complete: () => this._loading.set(false),
    });
  }

  private fetchSAE(dto: GeoInputDTO, geoType: string): void {
    console.log("FetchSAE "+geoType);
    dto.id=1;  // TODO remove these 3+2 rows
    dto.code="CC-06088";
    dto.resolution="HD";
    dto.hc = "HC";
    dto.time = 60;
    console.log(dto);
    this.fetchLoading();
    this.http.post<GeoTupleDTO>(`${environment.baseUrl}/sae/${geoType}`, dto).subscribe({    
      next: (res) => { this._geoTupleDTO.set(res); console.log(res); },
      error: (err) => {
        if(err.status == 404) console.log("Not found "+dto.code);
        else this.catchError(err);
        this._geoTupleDTO.set(emptyGeo);
      },
      complete: () => this._loading.set(false),
    });
  }
}
