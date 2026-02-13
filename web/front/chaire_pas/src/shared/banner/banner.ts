import { Component, computed, input } from '@angular/core';
// import { APP_BASE_HREF } from '@angular/common';

@Component({
  selector: 'app-banner',
  imports: [],
  templateUrl: './banner.html',
  styleUrl: './banner.scss',
})
export class Banner {
  title = "Chaire pour la prévention et l'accès aux soins";
  //baseHref = document.querySelector('base')?.getAttribute('href') ?? '';
}
