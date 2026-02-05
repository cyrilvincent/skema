import { Component, inject } from '@angular/core';
import { UserService } from '../user.service';

@Component({
  selector: 'app-admin',
  imports: [],
  templateUrl: './admin.html',
  styleUrl: './admin.scss',
})
export class Admin {

  userService = inject(UserService);

  constructor() {
    this.userService.isAdmin.set(true);
  }

}
