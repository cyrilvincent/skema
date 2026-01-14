import { Injectable, computed, signal } from '@angular/core';
import { Versions } from './about.interfaces';
import { environment} from '../../environments/environment'
import { CommonService } from '../../shared/common.service';


@Injectable({
  providedIn: 'root',
})
export class AboutService extends CommonService {

  _root = signal<string>(environment.loading);          
  _versions = signal<Versions>({icip: environment.loading, back: environment.loading}); 
  root = computed(() => this._root());       
  versions = computed(() => this._versions());
  
  fetchRoot(): void {
    this.fetchLoading();
    this.http.get<string>(`${environment.baseUrl}/`).subscribe({
      next: (res) => { this._root.set(res); },
      error: (err) => this.catchError(err),
      complete: () => this._loading.set(false),
    });
  }

  fetchVersions(): void {
    this.fetchLoading();
    this.http.get<Versions>(`${environment.baseUrl}/versions`).subscribe({
      next: (res) => { this._versions.set(res); },
      error: (err) => this.catchError(err),
      complete: () => this._loading.set(false),
    });
  }
  
}


