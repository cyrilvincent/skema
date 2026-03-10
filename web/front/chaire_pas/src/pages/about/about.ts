import { Component, ChangeDetectionStrategy } from '@angular/core';
import { Versions } from './versions/versions';


@Component({
  selector: 'app-about',
  imports: [Versions],
  templateUrl: './about.html',
  styleUrl: './about.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class About {
  

}
