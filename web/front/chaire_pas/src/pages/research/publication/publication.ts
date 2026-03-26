import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { PublicationService } from './publication.service';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-publication',
  imports: [MatIconModule],
  templateUrl: './publication.html',
  styleUrl: './publication.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Publication {

  service = inject(PublicationService);

  constructor() {
    this.service.getPublications();
    this.service.getWorks();
    //this.service.getStudies();
  }

}
