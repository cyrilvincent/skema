import { ChangeDetectionStrategy, Component, computed, effect, HostListener, inject, signal } from '@angular/core';
import { RouterOutlet, ActivatedRoute } from '@angular/router';
import { Menu } from "../shared/menu/menu";
import { Banner } from '../shared/banner/banner';
import { Footer } from "../shared/footer/footer";
import { Fullscreen } from '../pages/dataviz/fullscreen/fullscreen';
import { CommonService } from '../shared/common.service';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MenuService } from '../shared/menu/menu-service';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, Menu, Footer, Fullscreen, Banner, MatToolbarModule],
  templateUrl: './app.html',
  styleUrl: './app.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class App {
  activeMenu = signal(0);
  route = inject(ActivatedRoute);
  fullscreen = signal<boolean>(false);
  service = inject(CommonService);
  // isScrolled = signal(false);
  spacer = signal(this.getSpacer());
  isWhite = computed<boolean>(() => this.service.isMobile() || this.isHeroShrunk() || this.activeMenu()!=0)
  menuService = inject(MenuService);
  isHeroShrunk = signal(false);
  heroHeight = signal('100vh');

  constructor() {
    const usp = new URLSearchParams(window.location.search);
    this.fullscreen.set(usp.get("fullscreen") == "true");
    effect(() => {
      const nb = this.service.homeEvent();
      if (nb && nb > 0) {
        this.changeMenu(nb);
        this.service.homeEvent.set(0);
      };
    });
    effect(() => {
      this.service.isMobile();
      if (this.getSpacer() != this.spacer()) this.spacer.set(this.getSpacer());
    });
  }

  ngOnInit() {
    console.log("isMobile: "+this.service.isMobile())
  }

  menuChanged(nb: number) {
    this.activeMenu.set(nb);
    this.spacer.set(this.getSpacer());
  }

  changeMenu(nb: number) {
    this.menuService.changeMenu(nb);
    this.menuChanged(nb);
  }

  @HostListener('window:scroll', [])
  onWindowScroll(): void {
    const scrollY = window.scrollY;
    const heroHeight = window.innerHeight;
    this.isHeroShrunk.set(scrollY > heroHeight * 0.1);
    // const scrollTop = window.scrollY;
    // const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
    // const ratio = 1 - (scrollTop / maxScroll); // 1 → 0 en scrollant
    // const height = Math.max(0, ratio * 100);
    // console.log(height);
    // this.heroHeight.set(`${height}vh`);

  }

  getSpacer(): string {
    if (this.activeMenu() != 0) {
      if (this.service.isMobile()) return "mobile-top-spacer";
      else return "top-spacer";
    }
    if (this.service.isMobile()) return "mobile-top-spacer";
    else return "top-spacer-shrunk";
  }

}




