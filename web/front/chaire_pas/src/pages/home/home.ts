import { Component, inject } from '@angular/core';
import { CommonService } from '../../shared/common.service';

@Component({
  selector: 'app-home',
  imports: [],
  templateUrl: './home.html',
  styleUrl: './home.scss',
})
export class Home {

  service = inject(CommonService)

}
