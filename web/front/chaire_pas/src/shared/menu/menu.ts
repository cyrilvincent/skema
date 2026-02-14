import { Component, inject, output, signal } from '@angular/core';
import { RouterLinkWithHref, RouterLink } from '@angular/router';
import { MenuService } from './menu-service';
import { MatIconModule } from "@angular/material/icon";
import { CommonService } from '../common.service';

@Component({
  selector: 'app-menu-old',
  imports: [RouterLink, RouterLinkWithHref, MatIconModule],
  templateUrl: './menu.html',
  styleUrl: './menu.scss',
})
export class Menu {
  service = inject(MenuService);
  commonService = inject(CommonService);
  activeMenu = this.service.activeMenu; 
  menuChangedEvent = output<number>(); // Ne sert plus
  clicked = signal<boolean>(false);

  async changeMenu(nb: number) {
    this.service.changeMenu(nb);
    this.menuChangedEvent.emit(nb);
    await this.commonService.delay(200);
    this.clicked.set(true);
  }

  
}
