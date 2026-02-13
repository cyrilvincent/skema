import { Component, inject, ChangeDetectionStrategy } from '@angular/core';
import { Members } from './members/members';
import { Versions } from './versions/versions';


@Component({
  selector: 'app-about',
  imports: [Members, Versions],
  templateUrl: './about.html',
  styleUrl: './about.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class About {
  

}
