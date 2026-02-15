import { Component, inject } from '@angular/core';
import { CommonService } from '../../../shared/common.service';

@Component({
  selector: 'app-members',
  imports: [],
  templateUrl: './members.html',
  styleUrl: './members.scss',
})
export class Members {
  service = inject(CommonService);
}
