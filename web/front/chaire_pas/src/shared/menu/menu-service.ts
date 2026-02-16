import { Injectable, signal } from '@angular/core';
import { MenuItem, data } from './menu-data';

@Injectable({
  providedIn: 'root',
})
export class MenuService {

  activeMenu = signal(0);
  menu: MenuItem[] = data;

  changeMenu(nb: number) {
    this.activeMenu.set(nb);
  }




  
}
