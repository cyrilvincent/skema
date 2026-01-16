import { Component } from '@angular/core';
import { environment } from '../../environments/environment';

@Component({
  selector: 'app-footer',
  imports: [],
  templateUrl: './footer.html',
  styleUrl: './footer.scss',
})
export class Footer {

  copyright = environment.copyright;

}
