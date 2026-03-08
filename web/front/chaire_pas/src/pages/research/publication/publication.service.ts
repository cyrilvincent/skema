import { Injectable, signal } from '@angular/core';
import { PublicationDTO, publications } from "./publication.data"

@Injectable({
  providedIn: 'root',
})
export class PublicationService {

  publications = signal<PublicationDTO[]>([]);

  getPublications() {
    this.publications.set(publications.sort((a, b) => b.year - a.year));
  }
}
