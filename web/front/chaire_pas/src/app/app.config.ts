import { ApplicationConfig, provideBrowserGlobalErrorListeners, provideAppInitializer, inject } from '@angular/core';
import { provideRouter, withInMemoryScrolling } from '@angular/router';
import { routes } from './app.routes';
import { provideHttpClient, withInterceptors } from '@angular/common/http';

// @ts-ignore
import Plotly from 'plotly.js-dist-min'
import { PlotlyModule } from 'angular-plotly.js';
import { accountInterceptor } from '../shared/account/account.interceptor';
import { AccountService } from '../shared/account/account.service';

function initAnonymous(service: AccountService) {
  return () => {
    service.anonymous();
    service.checkLogged();
  }
}

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes,
      // withPreloading(PreloadAllModules),
      withInMemoryScrolling({
            anchorScrolling: 'enabled',
            scrollPositionRestoration: 'enabled',
          })
      ),
    provideHttpClient(withInterceptors([accountInterceptor])),
    provideAppInitializer(() => {
      const service = inject(AccountService);
      return initAnonymous(service)();
    }),
    ...PlotlyModule.forRoot(Plotly).providers ?? [],
  ]
};
