import { Routes } from '@angular/router';
import { About } from '../pages/about/about';
import { Home } from '../pages/home/home';
import { Dataviz } from '../pages/dataviz/dataviz';

export const routes: Routes = [
  {
    path: '',
    title: "Chaire pour la prévention et l'accès aux soins",
    component: Home,
  },
  {
    path: 'about',
    title: "A propos: Chaire pour la prévention et l'accès aux soins",
    component: About,
  },
  {
    path: 'dataviz',
    title: "Dataviz: Chaire pour la prévention et l'accès aux soins",
    component: Dataviz,
  },
]
