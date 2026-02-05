import { Injectable } from '@angular/core';
import { signal } from '@angular/core';

@Injectable({
  providedIn: 'root',
})
export class UserService {

  name = signal<string | null>(null);
  isAdmin = signal<boolean>(false);
  
}
