import { Component } from '@angular/core';
import { environment } from '../../environments/environment';

@Component({
  selector: 'app-banner',
  imports: [],
  templateUrl: './banner.html',
  styleUrl: './banner.scss',
})
export class Banner {
  title = environment.title;
}
