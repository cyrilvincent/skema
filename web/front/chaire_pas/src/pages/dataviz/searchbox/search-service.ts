import { computed, Injectable, signal } from '@angular/core';
import { CommonService } from '../../../shared/common.service';
import { environment } from '../../../environments/environment';
import { HttpParams } from '@angular/common/http';

@Injectable({
  providedIn: 'root',
})
export class SearchService extends CommonService {

  _codes = signal<[string, string][]>([]);          
  codes = computed(() => this._codes());

  fetchFind(q: string | null): void {
    let query = q?.trim() ?? '';
    if (query.length > 0) {
        console.log("FetchFind "+q);
        this.fetchLoading();
        this.http.get<[string, string][]>(`${environment.baseUrl}/find/${encodeURIComponent(query)}`).subscribe({
          next: (res) => { this._codes.set(res); },
          error: (err) => { this.catchError(err); this._codes.set([]) },
          complete: () => this._loading.set(false),
        });
      }
    }
  }


