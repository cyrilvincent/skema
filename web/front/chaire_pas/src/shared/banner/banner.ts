import { Component, inject, input } from '@angular/core';
import { environment } from '../../environments/environment';
import { CommonService } from '../common.service';

@Component({
  selector: 'app-banner',
  imports: [],
  templateUrl: './banner.html',
  styleUrl: './banner.scss',
})
export class Banner {
  title = environment.title;
  service = inject(CommonService);
  isWhite = input<boolean>(false);
}
