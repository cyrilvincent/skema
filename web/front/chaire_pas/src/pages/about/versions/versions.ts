import { Component, inject, VERSION } from '@angular/core';
import { environment } from '../../../environments/environment';
import { PlotlyModule } from 'angular-plotly.js';
// @ts-ignore
import Plotly from 'plotly.js-dist-min'
import pkg from 'angular-plotly.js/package.json' assert { type: 'json' }
import { AboutService } from './versions.service';

@Component({
  selector: 'app-versions',
  imports: [],
  templateUrl: './versions.html',
  styleUrl: './versions.scss',
})
export class Versions {
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
  backendVisible = false;

  backend() {
    this.backendVisible = !this.backendVisible;
    if (this.backendVisible) {
      this.aboutService.fetchRoot();
      this.aboutService.fetchVersions();
    }
  }
}
