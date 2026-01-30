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

  fetch(dto: GeoInputDTO, type: string): void {
    if (type == "APL") {
      this.fetchAPL(dto);
    } 
  }

  save(dto: GeoInputDTO, type: string, render: string) {
    if (type == "APL") {
      if (render == "json") this.saveAPLJSON(dto);
      else if (render == "csv") this.saveAPLCSV(dto);
    }
  }

  private fetchAPL(dto: GeoInputDTO): void {
    console.log("FetchAPL ");
    console.log(dto);
    this.fetchLoading();
    this.http.post<GeoTupleDTO>(`${environment.baseUrl}/apl/iris`, dto).subscribe({    
      next: (res) => { this._geoTupleDTO.set(res); },
      error: (err) => {
        if(err.status == 404) console.log("Not found "+dto.code);
        else this.catchError(err);
        this._geoTupleDTO.set(emptyGeo);
      },
      complete: () => this._loading.set(false),
    });
  }

  private saveAPLJSON(dto: GeoInputDTO): void {
    console.log("saveAPLJSON");
    console.log(dto);
    this.http.post<GeoTupleDTO>(`${environment.baseUrl}/apl/iris`, dto).subscribe({    
      next: (res) => {
        const blob = new Blob([JSON.stringify(res[1])], { type: 'application/json' });
        this.fileSaver.save(blob, `apl_iris_${dto.code}_${dto.id}_${dto.time}_${dto.hc}_${dto.exp}.json`);
      },
      error: (err) => {
        if(err.status == 404) console.log("Not found "+dto.code);
        else this.catchError(err);
      },
    });
  }

  private saveAPLCSV(dto: GeoInputDTO): void {
    console.log("saveAPLCSV");
    console.log(dto);
    this.http.post<string>(`${environment.baseUrl}/apl/iris/csv`, dto).subscribe({    
      next: (res) => {
        const blob = new Blob([res], { type: 'application/json' });
        this.fileSaver.save(blob, `apl_iris_${dto.code}_${dto.id}_${dto.time}_${dto.hc}_${dto.exp}.csv`);
      },
      error: (err) => {
        if(err.status == 404) console.log("Not found "+dto.code);
        else this.catchError(err);
      },
    });
  }
}
