import { Injectable, signal } from '@angular/core';

@Injectable({
  providedIn: 'root',
})
export class MenuService {

  activeMenu = signal(0);

  delay(delay: number) {
    return new Promise(r => {
      setTimeout(r, delay);
    })
  }

  changeMenu(nb: number) {
    this.activeMenu.set(nb);
  }




  
}
