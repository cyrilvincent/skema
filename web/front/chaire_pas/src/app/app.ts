import { Component, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { Menu } from "../shared/menu/menu";
import { Banner } from '../shared/banner/banner';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, Menu, Banner],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {
  title = "Chaire pour la prévention et l'accès aux soins";
  activeMenu = signal(0);

  menuChanged(nb: number) {
    this.activeMenu.set(nb);
  }
}
