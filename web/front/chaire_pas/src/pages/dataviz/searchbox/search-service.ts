import { computed, Injectable, signal } from '@angular/core';
import { CommonService } from '../../../shared/common.service';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class SearchService extends CommonService {

  apl_codes = signal<[string, string][]>([]);
  sae_codes = signal<[string, string][]>([]);

  fetchFind(q: string | null, type: string): void {
    let query = q?.trim() ?? '';
    if (query.length > 0) {
      console.log("FetchFind "+q);
      this.fetchLoading();
      this.http.get<[string, string][]>(`${environment.baseUrl}/find/${encodeURIComponent(query)}`).subscribe({
        next: (res) => { type == "APL" ? this.apl_codes.set(res) : this.sae_codes.set(res) },
        error: (err) => { 
          this.catchError(err); 
          type == "APL" ? this.apl_codes.set([]) : this.sae_codes.set([]) },
        complete: () => this._loading.set(false),
      });
    }
  }

  init() {
    this.apl_codes.set([]);
    this.sae_codes.set([]);
  }
}



