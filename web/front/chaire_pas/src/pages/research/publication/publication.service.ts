import { Injectable, signal } from '@angular/core';
import { PublicationDTO, publications, works, studies } from "./publication.data"

@Injectable({
  providedIn: 'root',
})
export class PublicationService {

  publications = signal<PublicationDTO[]>([]);
  works = signal<PublicationDTO[]>([]);
  studies = signal<PublicationDTO[]>([]);

  getPublications() {
    this.publications.set(publications.sort((a, b) => b.year! - a.year!));
  }

  getWorks() {
    this.works.set(works);
  }

  getStudies() {
    this.studies.set(studies.sort((a, b) => b.year! - a.year!));
  }
}
