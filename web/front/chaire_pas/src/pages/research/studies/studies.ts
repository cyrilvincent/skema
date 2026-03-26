import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { PublicationService } from '../publication/publication.service';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-studies',
  imports: [MatIconModule],
  templateUrl: './studies.html',
  styleUrl: './studies.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Studies {

  service = inject(PublicationService);

  constructor() {
    this.service.getStudies();
  }


}
