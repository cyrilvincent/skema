import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AccountService } from './account.service';

export const accountInterceptor: HttpInterceptorFn = (req, next) => {
  const token = inject(AccountService).getToken();
  const shouldSkip = req.url.includes('/auth/');
  if (token && !shouldSkip) {
    req = req.clone({
      setHeaders: { Authorization: `Bearer ${token}` }
    });
  }
  return next(req);
};



