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
    if (type == "APL") {
      if (geoType == "iris") this.fetchIrisAPL(dto);
      else this.fetchCommuneAPL(dto);
    } 
  }

  save(dto: GeoInputDTO, type: string, render: string, geoType: string) {
    if (type == "APL") {
      if (render == "json") {
        if (geoType == "iris") this.saveIrisAPLJSON(dto);
        else this.saveCommuneAPLJSON(dto);
      } 
      else if (render == "csv") {
        if (geoType == "iris") this.saveIrisAPLCSV(dto);
        else this.saveCommuneAPLCSV(dto);
      } 
    }
  }

  private fetchIrisAPL(dto: GeoInputDTO): void {
    console.log("FetchIrisAPL ");
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

    private fetchCommuneAPL(dto: GeoInputDTO): void {
    console.log("FetchCommuneAPL ");
    console.log(dto);
    this.fetchLoading();
    this.http.post<GeoTupleDTO>(`${environment.baseUrl}/apl/commune`, dto).subscribe({    
      next: (res) => { this._geoTupleDTO.set(res); },
      error: (err) => {
        if(err.status == 404) console.log("Not found "+dto.code);
        else this.catchError(err);
        this._geoTupleDTO.set(emptyGeo);
      },
      complete: () => this._loading.set(false),
    });
  }

  private saveIrisAPLJSON(dto: GeoInputDTO): void {
    console.log("saveIrisAPLJSON");
    console.log(dto);
    this.fetchLoading();
    this.http.post<GeoTupleDTO>(`${environment.baseUrl}/apl/iris`, dto).subscribe({    
      next: (res) => {
        const blob = new Blob([JSON.stringify(res[1])], { type: 'application/json' });
        this.fileSaver.save(blob, `apl_iris_${dto.code}_${dto.id}_${dto.time}_${dto.hc}_${dto.exp}.json`);
      },
      error: (err) => {
        if(err.status == 404) console.log("Not found "+dto.code);
        else this.catchError(err);
      },
      complete: () => this._loading.set(false),
    });
  }

    private saveCommuneAPLJSON(dto: GeoInputDTO): void {
    console.log("saveCommuneAPLJSON");
    console.log(dto);
    this.fetchLoading();
    this.http.post<GeoTupleDTO>(`${environment.baseUrl}/apl/commune`, dto).subscribe({    
      next: (res) => {
        const blob = new Blob([JSON.stringify(res[1])], { type: 'application/json' });
        this.fileSaver.save(blob, `apl_commune_${dto.code}_${dto.id}_${dto.time}_${dto.hc}_${dto.exp}.json`);
      },
      error: (err) => {
        if(err.status == 404) console.log("Not found "+dto.code);
        else this.catchError(err);
      },
      complete: () => this._loading.set(false),
    });
  }

  private saveIrisAPLCSV(dto: GeoInputDTO): void {
    console.log("saveIrisAPLCSV");
    console.log(dto);
    this.fetchLoading();
    this.http.post<string>(`${environment.baseUrl}/apl/iris/csv`, dto).subscribe({    
      next: (res) => {
        const blob = new Blob([res], { type: 'application/json' });
        this.fileSaver.save(blob, `apl_iris_${dto.code}_${dto.id}_${dto.time}_${dto.hc}_${dto.exp}.csv`);
      },
      error: (err) => {
        if(err.status == 404) console.log("Not found "+dto.code);
        else this.catchError(err);
      },
      complete: () => this._loading.set(false),
    });
  }

  private saveCommuneAPLCSV(dto: GeoInputDTO): void {
    console.log("saveCommuneAPLCSV");
    console.log(dto);
    this.fetchLoading();
    this.http.post<string>(`${environment.baseUrl}/apl/commune/csv`, dto).subscribe({    
      next: (res) => {
        const blob = new Blob([res], { type: 'application/json' });
        this.fileSaver.save(blob, `apl_commune_${dto.code}_${dto.id}_${dto.time}_${dto.hc}_${dto.exp}.csv`);
      },
      error: (err) => {
        if(err.status == 404) console.log("Not found "+dto.code);
        else this.catchError(err);
      },
      complete: () => this._loading.set(false),
    });
  }

  
}
