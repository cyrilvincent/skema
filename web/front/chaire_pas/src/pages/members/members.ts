import { Component, inject } from '@angular/core';
import { CommonService } from '../../shared/common.service';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-members',
  imports: [MatIconModule],
  templateUrl: './members.html',
  styleUrl: './members.scss',
})
export class Members {
  service = inject(CommonService);
}
