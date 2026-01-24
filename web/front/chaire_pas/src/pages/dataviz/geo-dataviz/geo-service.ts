import { computed, Injectable, signal } from '@angular/core';
import { CommonService } from '../../../shared/common.service';
import { GeoInputDTO } from '../dataviz.interfaces';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class GeoService  extends CommonService {
  _geojsonDTO = signal<GeoInputDTO | null>(null);          
  geojsonDTO = computed(() => this._geojsonDTO());

  fetch(dto: GeoInputDTO, type: string): void {
    if (type == "APL") {
    }
    else this.fetchSAE(dto);
  }

  fetchSAE(dto: GeoInputDTO): void {
    console.log("FetchSAE "+dto);
    // Cote back si len(df)==0 renvoyer une erreur 204 ou 418 et remettre le empty
    /*this.fetchLoading();
    this.http.post<ProfessionEtablissementDTO>(`${environment.baseUrl}/geo/sae`, dto).subscribe({
      next: (res) => { this._geojsonDTO.set(res); },
      error: (err) => { this.catchError(err); this._geojsonDTO.set(null) },
      complete: () => this._loading.set(false),
    });*/
  }
}
