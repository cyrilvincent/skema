import { computed, Injectable, signal } from '@angular/core';
import { CommonService } from '../../../shared/common.service';
import { GeoInputDTO, GeoTupleDTO } from '../dataviz.interfaces';
import { environment } from '../../../environments/environment';
import { emptyGeo } from '../dataviz.data';

@Injectable({
  providedIn: 'root',
})
export class GeoService  extends CommonService {
  _geoTupleDTO = signal<GeoTupleDTO>(emptyGeo);          
  geoTupleDTO = computed(() => this._geoTupleDTO());

  fetch(dto: GeoInputDTO, type: string): void {
    if (type == "APL") {
      this.fetchAPL(dto);
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
}
