import { Component, output, signal } from '@angular/core';
import { RouterLinkWithHref, RouterLink } from '@angular/router';

@Component({
  selector: 'app-menu-old',
  imports: [RouterLink, RouterLinkWithHref],
  templateUrl: './menu_old.html',
  styleUrl: './menu_old.scss',
})
export class MenuOld {
  activeMenu = signal(0);
  menuChangedEvent = output<number>();

  changeMenu(nb: number) {
    this.activeMenu.set(nb);
    this.menuChangedEvent.emit(nb);
  }
}
