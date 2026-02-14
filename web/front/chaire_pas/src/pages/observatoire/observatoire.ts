import { Component, inject } from '@angular/core';
import { RouterLink } from "@angular/router";
import { MenuService } from '../../shared/menu/menu-service';

@Component({
  selector: 'app-observatoire',
  imports: [RouterLink],
  templateUrl: './observatoire.html',
  styleUrl: './observatoire.scss',
})
export class Observatoire {

  menuService = inject(MenuService);

}
