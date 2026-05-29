import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AccountService } from './account.service';
import { environment } from '../../environments/environment';

export const accountGuard: CanActivateFn = () => {
  if (environment.production) {
    const auth = inject(AccountService);
    const router = inject(Router);
    if (auth.isLoggedIn()) return true;
    router.navigate(['/account']);
    return false;
  }
  return true;
};


