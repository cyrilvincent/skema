import { Component } from '@angular/core';
import { environment } from '../../../environments/environment';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-legal',
  imports: [MatIconModule],
  templateUrl: './legal.html',
  styleUrl: './legal.scss',
})
export class Legal {
  dns = environment.dns;
  title = environment.title;
}
