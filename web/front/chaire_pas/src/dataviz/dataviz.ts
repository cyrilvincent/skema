import { Component } from '@angular/core';

// @ts-ignore
import Plotly from 'plotly.js-dist-min'
import { PlotlyModule } from 'angular-plotly.js';


@Component({
  selector: 'app-dataviz',
  imports: [PlotlyModule],
  templateUrl: './dataviz.html',
  styleUrl: './dataviz.scss',
})
export class Dataviz {

  public constructor() {
    console.log('Plotly version =', (Plotly as any).version);
  }

  data = [
      { x: [1, 2, 3], y: [2, 6, 3], type: 'scatter', hoverinfo: 'text', mode: 'lines+markers', name: 'Série A' },
      { x: [1, 2, 3], y: [4, 1, 7], type: 'bar', name: 'Série B' },
    ];

  layout: Partial<Plotly.Layout> = {   
    title: { text: 'Mon premier graphique' },
    autosize: true,
    margin: { t: 40, r: 10, b: 40, l: 40 },
  };

  config: Partial<Plotly.Config> = {
    responsive: true,
    displayModeBar: true
  };

}
