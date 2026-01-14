import { Component, output, signal } from '@angular/core';
import { RouterLinkWithHref, RouterLink } from '@angular/router';

@Component({
  selector: 'app-menu',
  imports: [RouterLink, RouterLinkWithHref],
  templateUrl: './menu.html',
  styleUrl: './menu.scss',
})
export class Menu {
  activeMenu = signal(0);
  menuChangedEvent = output<number>();

  changeMenu(nb: number) {
    this.activeMenu.set(nb);
    this.menuChangedEvent.emit(nb);
  }
}
