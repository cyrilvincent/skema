import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { CommonService } from '../../shared/common.service';
import { MatIconModule } from '@angular/material/icon';
import { MenuService } from '../../shared/menu/menu-service';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-home',
  imports: [MatIconModule, RouterLink],
  templateUrl: './home.html',
  styleUrl: './home.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Home {

  service = inject(CommonService);
  menuService = inject(MenuService);

  changeMenu(nb: number) {
    this.menuService.changeMenu(nb);
    this.service.homeEvent.set(nb);
  }

}
