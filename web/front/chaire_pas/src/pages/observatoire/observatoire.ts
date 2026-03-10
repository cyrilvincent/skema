import { Component, inject } from '@angular/core';
import { RouterLink } from "@angular/router";
import { MenuService } from '../../shared/menu/menu-service';
import { CommonService } from '../../shared/common.service';
import { MatTooltip } from "@angular/material/tooltip";

@Component({
  selector: 'app-observatoire',
  imports: [RouterLink, MatTooltip],
  templateUrl: './observatoire.html',
  styleUrl: './observatoire.scss',
})
export class Observatoire {

  menuService = inject(MenuService);
  commonService = inject(CommonService);

}
