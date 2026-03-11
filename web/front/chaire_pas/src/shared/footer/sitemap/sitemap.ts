import { Component, inject } from '@angular/core';
import { MenuService } from '../../menu/menu-service';
import { RouterLink, RouterLinkWithHref } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-sitemap',
  imports: [RouterLink, RouterLinkWithHref, MatIconModule],
  templateUrl: './sitemap.html',
  styleUrl: './sitemap.scss',
})
export class Sitemap {
  service = inject(MenuService);
}
