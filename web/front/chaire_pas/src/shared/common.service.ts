import { computed, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';

export class CommonService {
  
  http = inject(HttpClient);         
  _loading = signal<boolean>(false);
  _error = signal<string | null>(null);    
  loading = computed(() => this._loading());
  error = computed(() => this._error());
  
  fetchLoading() {
    this._loading.set(true);
    this._error.set(null);
  }

  catchError(err: any) {
    const msg = (typeof err?.error === 'string' && err.error) || err?.error?.message || err?.error?.detail || `HTTP ${err?.status ?? '??'}`;
    this._error.set(msg);
    this._loading.set(false);
  }

 

  
}


