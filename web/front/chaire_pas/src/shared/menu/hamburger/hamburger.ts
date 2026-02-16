import { Component, input } from '@angular/core';

@Component({
  selector: 'app-hamburger',
  imports: [],
  templateUrl: './hamburger.html',
  styleUrl: './hamburger.scss',
})
export class Hamburger {
  visible = input<boolean>(false);
}
