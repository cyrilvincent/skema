import { Component, VERSION } from '@angular/core';
import { environment } from '../environments/environment';
// @ts-ignore
import Plotly from 'plotly.js-dist-min'
import { PlotlyModule } from 'angular-plotly.js';
import pkg from 'angular-plotly.js/package.json' assert { type: 'json' }

@Component({
  selector: 'app-about',
  imports: [PlotlyModule],
  templateUrl: './about.html',
  styleUrl: './about.scss',
})
export class About {
  protected readonly version = environment.version;
  protected readonly copyright = environment.copyright;
  protected readonly plotlyVersion = (Plotly as any).version;
  protected readonly angularPlotlyVersion = pkg.version;
  protected readonly angularVersion = VERSION.full;
  protected readonly isCDN = false;


}
