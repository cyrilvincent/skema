import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { Login } from './login/login';
import { AccountService } from './account.service';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-account',
  imports: [Login, FormsModule, MatButtonModule],
  templateUrl: './account.html',
  styleUrl: './account.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Account {
  service = inject(AccountService);
}
