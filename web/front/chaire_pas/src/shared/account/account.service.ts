import { Injectable, signal } from '@angular/core';

@Injectable({
  providedIn: 'root',
})
export class AccountService {
  
  isLogged = signal(false);

  login(login: string, pwd: string) {
    if(login == "admin" && pwd == "EMlait$iA$0610") {
      console.log("Login ok")
      this.isLogged.set(true);
    }
    else console.log("Login ko");
  }
}
