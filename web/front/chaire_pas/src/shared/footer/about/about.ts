import { Component, ChangeDetectionStrategy } from '@angular/core';
import { Versions } from './versions/versions';
import { environment } from '../../../environments/environment';


@Component({
  selector: 'app-about',
  imports: [Versions],
  templateUrl: './about.html',
  styleUrl: './about.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class About {
  title = environment.title;
  accessibilite = environment.accessibilite;
}
