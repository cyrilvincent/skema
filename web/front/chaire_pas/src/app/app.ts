import { Component, computed, inject, signal } from '@angular/core';
import { RouterOutlet, ActivatedRoute } from '@angular/router';
import { Menu } from "../shared/menu/menu";
import { Banner } from '../shared/banner/banner';
import { Footer } from "../shared/footer/footer";
import { Fullscreen } from '../pages/dataviz/fullscreen/fullscreen';
import { CommonService } from '../shared/common.service';
import { MatToolbarModule } from '@angular/material/toolbar';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, Menu, Footer, Fullscreen, Banner, MatToolbarModule],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {
  activeMenu = signal(0);
  route = inject(ActivatedRoute);
  fullscreen = signal<boolean>(false);
  service = inject(CommonService);

  constructor() {
    const usp = new URLSearchParams(window.location.search);
    this.fullscreen.set(usp.get("fullscreen") == "true");
  }

  ngOnInit() {
    console.log("isMobile: "+this.service.isMobile())
  }

  menuChanged(nb: number) {
    this.activeMenu.set(nb);
  }

}




