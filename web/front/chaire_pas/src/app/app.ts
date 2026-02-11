import { Component, computed, inject, signal } from '@angular/core';
import { RouterOutlet, ActivatedRoute } from '@angular/router';
import { MenuOld } from "../shared/menu/menu_old";
// import { Banner } from '../shared/banner/banner';
import { Footer } from "../shared/footer/footer";
import { Fullscreen } from '../pages/dataviz/fullscreen/fullscreen';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, MenuOld, Footer, Fullscreen],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {
  title = "Chaire pour la prévention et l'accès aux soins";
  activeMenu = signal(0);
  route = inject(ActivatedRoute);
  fullscreen = signal<boolean>(false);

  constructor() {
    const usp = new URLSearchParams(window.location.search);
    this.fullscreen.set(usp.get("fullscreen") == "true");
  }

  menuChanged(nb: number) {
    this.activeMenu.set(nb);
  }
}

// TODO
// +---------------------------+
// | ☰  App title              |  ← mat-toolbar
// +------+--------------------+
// | Menu | Contenu principal  |  ← mat-sidenav + mat-sidenav-content
// |      |                    |
// +------+--------------------+

// ✅ Bonnes pratiques Material
// Menu = mat-nav-list
// Icône hamburger = menu
// Ne jamais faire ça à la main avec du CSS
// Toujours utiliser BreakpointObserver

// HTML
// // 
// <mat-sidenav-container class="sidenav-container">

//   <!-- Menu gauche -->
//   <mat-sidenav
//     #sidenav
//     [mode]="isMobile ? 'over' : 'side'"
//     [opened]="!isMobile">

//     <mat-nav-list>
//       <a mat-list-item routerLink="/home">Home</a>
//       <a mat-list-item routerLink="/map">Map</a>
//       <a mat-list-item routerLink="/settings">Settings</a>
//     </mat-nav-list>
//   </mat-sidenav>

// .ts

// import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';

// @Component({
//   selector: 'app-layout',
//   templateUrl: './layout.component.html'
// })
// export class LayoutComponent {
//   isMobile = false;

//   constructor(private breakpointObserver: BreakpointObserver) {
//     this.breakpointObserver
//       .observe([Breakpoints.Handset])
//       .subscribe(result => {
//         this.isMobile = result.matches;
//       });
//   }
// }

// CSS

// .sidenav-container {
//   height: 100vh;
// }

// .content {
//   padding: 16px;
// }


