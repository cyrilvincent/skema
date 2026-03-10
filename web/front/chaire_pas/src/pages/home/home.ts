import { Component, inject } from '@angular/core';
import { CommonService } from '../../shared/common.service';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-home',
  imports: [MatIconModule],
  templateUrl: './home.html',
  styleUrl: './home.scss',
})
export class Home {

  service = inject(CommonService)

}
