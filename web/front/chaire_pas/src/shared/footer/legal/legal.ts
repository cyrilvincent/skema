import { Component } from '@angular/core';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-legal',
  imports: [],
  templateUrl: './legal.html',
  styleUrl: './legal.scss',
})
export class Legal {
  dns = environment.dns;
  title = environment.title;
}
