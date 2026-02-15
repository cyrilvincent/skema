import { Component, inject } from '@angular/core';
import { environment } from '../../environments/environment';
import { CommonService } from '../common.service';

@Component({
  selector: 'app-footer',
  imports: [],
  templateUrl: './footer.html',
  styleUrl: './footer.scss',
})
export class Footer {
  copyright = environment.copyright;
  service = inject(CommonService);
}
