import { Component, output, signal } from '@angular/core';
import { RouterLinkWithHref, RouterLink } from '@angular/router';

@Component({
  selector: 'app-menu-old',
  imports: [RouterLink, RouterLinkWithHref],
  templateUrl: './menu.html',
  styleUrl: './menu.scss',
})
export class Menu {
  activeMenu = signal(0);
  menuChangedEvent = output<number>();
  clicked = signal<boolean>(false);

  changeMenu(nb: number) {
    this.activeMenu.set(nb);
    this.menuChangedEvent.emit(nb);
    this.clicked.set(true);
  }
}
