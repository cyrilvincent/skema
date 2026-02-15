import { Component, inject } from '@angular/core';
import { CommonService } from '../../shared/common.service';

@Component({
  selector: 'app-sustain',
  imports: [],
  templateUrl: './sustain.html',
  styleUrl: './sustain.scss',
})
export class Sustain {
  service = inject(CommonService);
}
