import { Component } from '@angular/core';
import { environment } from '../environments/environment';

@Component({
  selector: 'app-about',
  imports: [],
  templateUrl: './about.html',
  styleUrl: './about.scss',
})
export class About {
  protected readonly version = environment.version;
  protected readonly copyright = environment.copyright;
}
