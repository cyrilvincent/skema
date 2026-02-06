import { computed, Injectable, signal } from '@angular/core';
import { CommonService } from '../../../shared/common.service';
import { environment } from '../../../environments/environment';

// @Injectable({
//   providedIn: 'root',
// })
export class SearchService extends CommonService {

  codes = signal<[string, string][]>([]);

  fetchFind(q: string | null): void {
    let query = q?.trim() ?? '';
    if (query.length > 0) {
      console.log("FetchFind "+q);
      this.fetchLoading();
      this.http.get<[string, string][]>(`${environment.baseUrl}/find/${encodeURIComponent(query)}`).subscribe({
        next: (res) => { this.codes.set(res);},
        error: (err) => { 
          this.catchError(err); 
          this.codes.set([]);
        },
        complete: () => this._loading.set(false),
      });
    }
  }

  // init() {
  //   this.apl_codes.set([]);
  //   this.sae_codes.set([]);
  // }
}



