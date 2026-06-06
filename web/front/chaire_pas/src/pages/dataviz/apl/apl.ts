import { ChangeDetectionStrategy, Component } from '@angular/core';
import { Dataviz } from '../dataviz';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-apl',
  imports: [Dataviz, MatIconModule],
  templateUrl: './apl.html',
  styleUrl: './apl.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Apl {

}
