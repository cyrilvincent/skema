import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AccountService } from './account.service';

// Non utilisé
export const accountGuard: CanActivateFn = () => {
  const auth = inject(AccountService);
  const router = inject(Router);
  if (auth.isLoggedIn()) return true;
  router.navigate(['/account']);
  return false;
};

