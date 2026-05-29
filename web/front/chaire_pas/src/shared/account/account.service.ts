import { computed, Injectable, signal } from '@angular/core';
import { CommonService } from '../common.service';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class AccountService extends CommonService {
  
  isLogged = signal(this.isLoggedIn());

  // login(login: string, pwd: string) { // A rempalcer par la méthode ci dessous
  //   if(login == "admin" && pwd == "EMlait$iA$0610") {
  //     console.log("Login ok")
  //     this.isLogged.set(true);
  //   }
  //   else console.log("Login ko");
  // }

  login(user: string, password: string) {
    this.fetchLogin(user, password);
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

  logout() {
    this.isLogged.set(false);
    localStorage.removeItem('token');
  }

  getToken(): string | null {
    return localStorage.getItem('token');
  }

  isLoggedIn(): boolean {
    const token = this.getToken();
    if (!token) {
      return false;
    }
    const payload = JSON.parse(atob(token.split('.')[1]));
    const valid = payload.exp * 1000 > Date.now();
    if (!valid) console.log("Token expired");
    return valid;
  }

  checkLogged() {
    this.isLogged.set(this.isLoggedIn());
  }



  
}
