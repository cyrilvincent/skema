import { Injectable, signal } from '@angular/core';
import { CommonService } from '../common.service';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class AccountService extends CommonService {
  
  isLogged = signal(this.isLoggedIn());

  login(user: string, password: string) {
    this.fetchLogin(user, password);
  }

  anonymous() {
    if (!this.isValidAnonymousToken()) {
      this.fetchAnonymous();
    }
  }

  private fetchLogin(user: string, password: string) {
    console.log("fetchLogin " + user);
    this.fetchLoading();
    this.http.post<{ access_token: string }>(`${environment.baseUrl}/auth/login`, { "username": user, "password": password }).subscribe({
      next: (res) => {
        console.log("fetchLogin ok " + res.access_token);
        localStorage.setItem('token', res.access_token);
        this.isLogged.set(true);
      },
      error: (err) => {
        console.log("fetchLogin ko");
        this.isLogged.set(false);
        if(err.status == 404) console.log("Not found "+user);
        else this.catchError(err);        
      },
      complete: () => this._loading.set(false),
    });
  }

  private fetchAnonymous() {
    console.log("fetchAnonymous");
    this.fetchLoading();
    this.http.post<{ access_token: string }>(`${environment.baseUrl}/auth/guest`, {}).subscribe({
      next: (res) => {
        console.log("fetchAnonymous ok " + res.access_token);
        localStorage.setItem('anonymousToken', res.access_token);
      },
      error: (err) => {
        console.log("fetchAnonymous ko");
        if(err.status == 404) console.log("Not found ");
        else this.catchError(err);        
      },
      complete: () => this._loading.set(false),
    });
  }

  logout() {
    this.isLogged.set(false);
    localStorage.removeItem('token');
  }

  removeAnymous() {
    localStorage.removeItem('anonymousToken');
  }

  getToken(): string | null {
    return localStorage.getItem('token');
  }

  getAnonymousToken(): string | null {
    return localStorage.getItem('anonymousToken');
  }

  isLoggedIn(): boolean {
    const token = this.getToken();
    return this.isValidToken(token);
  }

  isValidAnonymousToken(): boolean {
    const token = this.getAnonymousToken();
    return this.isValidToken(token);
  }

  private isValidToken(token: string | null): boolean {
    if (!token) return false;
    const payload = JSON.parse(atob(token.split('.')[1]));
    let valid = payload.exp * 1000 > Date.now();
    if (!valid) console.log("Token expired");
    // if (valid && payload.version) {
    //   valid = payload.version == "1.0";
    //   if (!valid) console.log("Token bad version " + payload.version);
    //   this.removeAnymous();
    // }
    return valid;
  }

  checkLogged() {
    this.isLogged.set(this.isLoggedIn());
  }



  
}
