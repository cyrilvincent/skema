import { Injectable, computed, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Versions } from './about.interfaces';
import { environment} from '../environments/environment'


@Injectable({
  providedIn: 'root',
})
export class AboutService {

  http = inject(HttpClient);
  _root = signal<string>('');          
  _loading = signal<boolean>(false);
  _error = signal<string | null>(null);
  _versions = signal<Versions | null>(null);
  root = computed(() => this._root());        
  loading = computed(() => this._loading());
  error = computed(() => this._error());
  versions = computed(() => this._versions());
  
  fetchRoot(): void {
    this._loading.set(true);
    this._error.set(null);
    this.http.get<string>(`${environment.baseUrl}/`).subscribe({
      next: (res) => { this._root.set(res); },
      error: (err) => this.catchError(err),
      complete: () => this._loading.set(false),
    });
  }

  fetchVersions(): void {
    this._loading.set(true);
    this._error.set(null);
    this.http.get<Versions>(`${environment.baseUrl}/versions`).subscribe({
      next: (res) => { this._versions.set(res); },
      error: (err) => this.catchError(err),
      complete: () => this._loading.set(false),
    });
  }

  catchError(err: any) {
    const msg = (typeof err?.error === 'string' && err.error) || err?.error?.message || err?.error?.detail || `HTTP ${err?.status ?? '??'}`;
    this._error.set("from about.service: " + msg);
  }

  
}


