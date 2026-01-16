import { Component, computed, input } from '@angular/core';
// import { APP_BASE_HREF } from '@angular/common';

@Component({
  selector: 'app-banner',
  imports: [],
  templateUrl: './banner.html',
  styleUrl: './banner.scss',
})
export class Banner {
  //baseHref = document.querySelector('base')?.getAttribute('href') ?? '';
  activeMenu = input<number>(0);
  activeImage = computed(() => `background-image: url('img/banner${this.activeMenu()}.jpg');background-position: 50.00% ${this.activePosition()}%;`)
  texts = ["Les missions de la Chaire", 
    "L'observatoire de l'accès aux soins",
    "Nos projets scientifiques",
    "Open Data",
    "On parle de nous",
    "Soutenir la Chaire",
  ];
  activeText = computed(() => this.texts[this.activeMenu()]);
  positions = [78.11, 50, 46.44, 83.89, 50, 65.6];
  activePosition = computed(() => this.positions[this.activeMenu()]);

  // constructor() {
  //   console.log(this.baseHref);
  // }
}
