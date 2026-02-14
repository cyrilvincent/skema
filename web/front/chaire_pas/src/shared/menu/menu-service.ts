import { Injectable, signal } from '@angular/core';

@Injectable({
  providedIn: 'root',
})
export class MenuService {

  activeMenu = signal(0);

  changeMenu(nb: number) {
    this.activeMenu.set(nb);
  }




  
}
