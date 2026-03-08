import { Component, inject } from '@angular/core';
import { CommonService } from '../../shared/common.service';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-sustain',
  imports: [MatIconModule],
  templateUrl: './sustain.html',
  styleUrl: './sustain.scss',
})
export class Sustain {
  service = inject(CommonService);
}
