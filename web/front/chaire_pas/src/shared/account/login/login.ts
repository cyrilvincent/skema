import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormControl, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { AccountService } from '../account.service';

@Component({
  selector: 'app-login',
  imports: [MatInputModule, FormsModule, ReactiveFormsModule, MatButtonModule, MatIconModule],
  templateUrl: './login.html',
  styleUrl: './login.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Login {
  hide = signal(true);
  loginControl = new FormControl<string>("");
  pwdControl = new FormControl<string>("");
  login = signal("")
  pwd = signal("")
  service = inject(AccountService);
  badLogin = signal(false);

  ngOnInit() {
    this.loginControl.valueChanges.subscribe(
      s => this.login.set(s!)
    )
    this.pwdControl.valueChanges.subscribe(
      s => this.pwd.set(s!)
    )
  }

  clickEvent(event: MouseEvent) {
    this.hide.set(!this.hide());
    event.stopPropagation();
  }

  buttonClicked() {
    this.service.login(this.login(), this.pwd());
    this.badLogin.set(!this.service.isLogged())!
  }

  
}
