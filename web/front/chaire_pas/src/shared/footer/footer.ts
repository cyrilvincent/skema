import { Component, inject } from '@angular/core';
import { environment } from '../../environments/environment';
import { CommonService } from '../common.service';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-footer',
  imports: [RouterLink],
  templateUrl: './footer.html',
  styleUrl: './footer.scss',
})
export class Footer {
  copyright = environment.copyright;
  service = inject(CommonService);
  accessibilite = environment.accessibilite;
}
