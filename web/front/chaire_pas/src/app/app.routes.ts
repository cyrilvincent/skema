import { Routes } from '@angular/router';
import { About } from '../pages/about/about';
import { Home } from '../pages/home/home';
import { Observatoire } from '../pages/observatoire/observatoire';
import { Dataviz } from '../pages/dataviz/dataviz';
import { Admin } from '../shared/admin/admin';
import { Data } from '../pages/data/data';
import { Research } from '../pages/research/research';
import { Sustain } from '../pages/sustain/sustain';
import { Media } from '../pages/media/media';

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
    component: About,
  },
  {
    path: 'data',
    title: "Dataviz: Chaire pour la prévention et l'accès aux soins",
    component: Data,
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
