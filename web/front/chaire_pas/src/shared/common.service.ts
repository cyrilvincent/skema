import { computed, inject, Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';
import { toSignal } from '@angular/core/rxjs-interop';
import { map } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class CommonService {
  
  http = inject(HttpClient);         
  _loading = signal<boolean>(false);
  _error = signal<string | null>(null);    
  loading = computed(() => this._loading());
  error = computed(() => this._error());
  _breakpointObserver = inject(BreakpointObserver);
  
  fetchLoading() {
    this._loading.set(true);
    this._error.set(null);
  }

  catchError(err: any) {
    const msg = (typeof err?.error === 'string' && err.error) || err?.error?.message || err?.error?.detail || `HTTP ${err?.status ?? '??'}`;
    this._error.set(msg);
    this._loading.set(false);
  }

  delay(delay: number) {
    return new Promise(r => {
      setTimeout(r, delay);
    })
  }

  isMobile = toSignal(
    this._breakpointObserver
      .observe([Breakpoints.XSmall, Breakpoints.Small])
      .pipe(map(result => result.matches)),
    { initialValue: false }
  );
 
}


