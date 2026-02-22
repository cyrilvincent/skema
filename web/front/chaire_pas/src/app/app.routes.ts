import { Routes } from '@angular/router';
//import { About } from '../pages/about/about';
import { Home } from '../pages/home/home';
import { Observatoire } from '../pages/observatoire/observatoire';
import { Admin } from '../shared/admin/admin';
import { Data } from '../pages/data/data';
import { Research } from '../pages/research/research';
import { Sustain } from '../pages/sustain/sustain';
import { Media } from '../pages/media/media';
//import { Sae } from '../pages/sae/sae';
//import { Apl } from '../pages/apl/apl';

export const routes: Routes = [
  {
    path: '',
    title: "Missions: Chaire pour la prévention et l'accès aux soins",
    component: Home,
  },
  {
    path: 'observatoire',
    title: "L'Observatoire: Chaire pour la prévention et l'accès aux soins",
    component: Observatoire,
  },
  {
    path: 'about',
    title: "A propos: Chaire pour la prévention et l'accès aux soins",
    loadComponent: () =>
      import('../pages/about/about').then((m) => m.About),
  },
  {
    path: 'data',
    title: "Dataviz: Chaire pour la prévention et l'accès aux soins",
    component: Data,
  },
  {
    path: 'sae',
    title: "SAE: Chaire pour la prévention et l'accès aux soins",
    //component: Sae,
    loadComponent: () =>
      import('../pages/sae/sae').then((m) => m.Sae),
  },
  {
    path: 'apl',
    title: "APL: Chaire pour la prévention et l'accès aux soins",
    //component: Apl,
    loadComponent: () =>
      import('../pages/apl/apl').then((m) => m.Apl),
  },
  {
    path: 'research',
    title: "Recherche: Chaire pour la prévention et l'accès aux soins",
    component: Research,
  },
  {
    path: 'sustain',
    title: "Nous soutenir: Chaire pour la prévention et l'accès aux soins",
    component: Sustain,
  },
  {
    path: 'media',
    title: "Medias: Chaire pour la prévention et l'accès aux soins",
    component: Media,
  },
  {
    path: 'e0206m2205',
    title: "Admin",
    component: Admin,
  },

]
