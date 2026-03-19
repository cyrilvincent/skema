// hero-header.component.ts
import { Component, HostListener, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-hero-header',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './hero-header.component.html',
  styleUrls: ['./hero-header.component.scss']
})
export class HeroHeaderComponent {

  isScrolled = false;
  isHeroShrunk = false;

  @HostListener('window:scroll', [])
  onWindowScroll(): void {
    const scrollY = window.scrollY;
    const heroHeight = window.innerHeight;

    this.isHeroShrunk = scrollY > heroHeight * 0.1;
    this.isScrolled = scrollY > 50;
  }
}
