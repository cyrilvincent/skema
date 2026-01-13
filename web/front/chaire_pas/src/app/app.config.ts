import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideRouter } from '@angular/router';
import { routes } from './app.routes';
import { provideHttpClient, withInterceptors } from '@angular/common/http';

// @ts-ignore
import Plotly from 'plotly.js-dist-min'
import { PlotlyModule } from 'angular-plotly.js';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    provideHttpClient(),
    ...PlotlyModule.forRoot(Plotly).providers ?? [],

  ]
};

// TODO dans interceptors/error.interceptor
// import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
// import { throwError } from 'rxjs';
// import { catchError } from 'rxjs/operators';
// import { extractHttpErrorMessage } from '../utils/http-error.util';

// export const errorsInterceptor: HttpInterceptorFn = (req, next) => {
//   return next(req).pipe(
//     catchError((err: unknown) => {
//       if (err instanceof HttpErrorResponse) {
//         const msg = extractHttpErrorMessage(err);
//         // Ici: logger, toasts, Sentry, etc.
//         return throwError(() => new Error(msg));
//       }
//       return throwError(() => err);
//     })
//   );
// };


// import { provideHttpClient, withInterceptors } from '@angular/common/http';
// import { errorsInterceptor } from './core/interceptors/errors.interceptor';

// export const appConfig: ApplicationConfig = {
//   providers: [
//     provideHttpClient(withInterceptors([errorsInterceptor])),
//   ],
// };




