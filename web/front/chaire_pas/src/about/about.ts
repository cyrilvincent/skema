import { Component, inject, ChangeDetectionStrategy, VERSION } from '@angular/core';
import { environment } from '../environments/environment';
// @ts-ignore
import Plotly from 'plotly.js-dist-min'
import { PlotlyModule } from 'angular-plotly.js';
import pkg from 'angular-plotly.js/package.json' assert { type: 'json' }
import { AboutService } from './about.service';
import { AsyncPipe} from '@angular/common';
import { Observable } from 'rxjs';
import { NgIf } from '@angular/common';

@Component({
  selector: 'app-about',
  imports: [PlotlyModule],
  templateUrl: './about.html',
  styleUrl: './about.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class About {
  version = environment.version;
  copyright = environment.copyright;
  plotlyVersion = (Plotly as any).version;
  angularPlotlyVersion = pkg.version;
  angularVersion = VERSION.full;
  isCDN = false;
  aboutService = inject(AboutService)
  root = this.aboutService.root;       
  loading = this.aboutService.loading;   
  error = this.aboutService.error;
  versions = this.aboutService.versions;

  constructor() {
    this.aboutService.fetchRoot();
    this.aboutService.fetchVersions();
  }

}
