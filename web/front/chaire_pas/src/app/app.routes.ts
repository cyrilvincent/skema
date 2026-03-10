import { Routes } from '@angular/router';
//import { About } from '../pages/about/about';
import { Home } from '../pages/home/home';
import { Observatoire } from '../pages/observatoire/observatoire';
import { Admin } from '../shared/admin/admin';
import { Research } from '../pages/research/research';
import { Sustain } from '../pages/sustain/sustain';
import { environment } from '../environments/environment';
import { Publication } from '../pages/research/publication/publication';
import { Members } from '../pages/members/members';
import { Partners } from '../pages/partners/partners';
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
    path: 'sae',
    title: "Accessibilité aux soins hospitaliers: "+environment.title,
    //component: Sae,
    loadComponent: () =>
      import('../pages/dataviz/sae/sae').then((m) => m.Sae),
  },
  {
    path: 'sae2',
    title: "Accessibilité aux autres services de santé: "+environment.title,
    //component: Sae,
    loadComponent: () =>
      import('../pages/dataviz/sae/sae2').then((m) => m.Sae2),
  },
  {
    path: 'apl',
    title: "Accessibilité aux soins de premier recours: "+environment.title,
    //component: Apl,
    loadComponent: () =>
      import('../pages/dataviz/apl/apl').then((m) => m.Apl),
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
    path: 'partners',
    title: "Partenaires: "+environment.title,
    component: Partners,
  },
  {
    path: 'publication',
    title: "Publications: "+environment.title,
    component: Publication,
  },
  {
    path: 'members',
    title: "Equipe: "+environment.title,
    component: Members,
  },
  {
    path: 'e0206m2205',
    title: "Admin",
    component: Admin,
  },

]
