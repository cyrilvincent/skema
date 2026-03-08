import { Routes } from '@angular/router';
//import { About } from '../pages/about/about';
import { Home } from '../pages/home/home';
import { Observatoire } from '../pages/observatoire/observatoire';
import { Admin } from '../shared/admin/admin';
import { Data } from '../pages/data/data';
import { Research } from '../pages/research/research';
import { Sustain } from '../pages/sustain/sustain';
import { Media } from '../pages/media/media';
import { environment } from '../environments/environment';
import { Publication } from '../pages/research/publication/publication';
//import { Sae } from '../pages/sae/sae';
//import { Apl } from '../pages/apl/apl';

export const routes: Routes = [
  {
    path: '',
    title: "Missions: "+environment.title,
    component: Home,
  },
  {
    path: 'observatoire',
    title: "L'Observatoire: "+environment.title,
    component: Observatoire,
  },
  {
    path: 'about',
    title: "A propos: "+environment.title,
    loadComponent: () =>
      import('../pages/about/about').then((m) => m.About),
  },
  {
    path: 'data',
    title: "Dataviz: "+environment.title,
    component: Data,
  },
  {
    path: 'sae',
    title: "SAE: "+environment.title,
    //component: Sae,
    loadComponent: () =>
      import('../pages/sae/sae').then((m) => m.Sae),
  },
  {
    path: 'apl',
    title: "APL: "+environment.title,
    //component: Apl,
    loadComponent: () =>
      import('../pages/apl/apl').then((m) => m.Apl),
  },
  {
    path: 'research',
    title: "Recherche: "+environment.title,
    component: Research,
  },
  {
    path: 'sustain',
    title: "Nous soutenir: "+environment.title,
    component: Sustain,
  },
  {
    path: 'media',
    title: "Medias: "+environment.title,
    component: Media,
  },
  {
    path: 'publication',
    title: "Publications: "+environment.title,
    component: Publication,
  },
  {
    path: 'e0206m2205',
    title: "Admin",
    component: Admin,
  },

]
