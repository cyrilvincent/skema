import { Component, inject } from '@angular/core';
import { AccountService } from '../account/account.service';

@Component({
  selector: 'app-admin',
  imports: [],
  templateUrl: './admin.html',
  styleUrl: './admin.scss',
})
export class Admin {

  service = inject(AccountService);
  

}
