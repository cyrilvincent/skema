import { ApplicationConfig, provideBrowserGlobalErrorListeners, provideAppInitializer } from '@angular/core';
import { provideRouter } from '@angular/router';
import { routes } from './app.routes';

// @ts-ignore
import Plotly from 'plotly.js-dist-min'
import { PlotlyModule } from 'angular-plotly.js';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    ...PlotlyModule.forRoot(Plotly).providers ?? [],
    
    // provideAppInitializer(() => {
    //   return import('plotly.js-dist-min').then(({ default: Plotly }) => {
    //     (PlotlyModule as any).plotlyjs = Plotly;
    //     console.log('Plotly chargé, version =', (Plotly as any).version);
    //   });
    // }),


  ]
};



