import { ChangeDetectionStrategy, Component } from '@angular/core';
import { Dataviz } from '../dataviz';

@Component({
  selector: 'app-apl',
  imports: [Dataviz],
  templateUrl: './apl.html',
  styleUrl: './apl.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Apl {

}
