import { Component, computed, effect, inject, input, signal } from '@angular/core';
import { PlotlyModule } from 'angular-plotly.js';
import { GeoInputDTO, GeoTupleDTO, GeoDTO, GeoYearDTO } from '../dataviz.interfaces';
import { emptyGeo } from '../dataviz.data';
import { GeoService } from './geo-service';

@Component({
  selector: 'app-geo-dataviz',
  imports: [PlotlyModule],
  templateUrl: './geo-dataviz.html',
  styleUrl: './geo-dataviz.scss',
})
export class GeoDataviz {
  service = inject(GeoService);
  values = this.service.geoTupleDTO;
  loading = this.service.loading;
  dto = input<GeoInputDTO | null>(null);
  type = input<string>("APL");
  geoType = input<string>("iris");
  df = computed<GeoDTO>(() => this.values()[0]);
  years = computed<{[key: string]: GeoYearDTO}>(() =>  this.df()["years"]);
  firstYear = computed<string>(() => Object.keys(this.years())[0]);
  layout = computed<Partial<Plotly.Layout>>(() => this.getLayout()); 
  config = signal<Partial<Plotly.Config>>(this.getConfig());
  data = computed<any[]>(() =>  [this.getGeo(), this.getScatter() as any]);
  visible = computed<boolean>(() => this.df()["center_lon"] != 0);

  constructor() {
    effect(() => this.onInputDTOChanged(this.dto()));
  }

  onInputDTOChanged(dto: GeoInputDTO | null) {
    if (dto != null) {
      console.log("onInputDTOchanged");
      console.log(dto);
      this.service.fetch(dto, this.type());
    }
  }

  getTexts(): String[][] {
    const texts: string[][] = [];
    for (const year of Object.keys(this.years())) {
      const df_year = this.years()[year];
      let text = df_year["code_iris"].map((ci, i) => `
Commune: ${df_year["nom_commune"][i]}<br>
Nom Iris: ${df_year["nom_iris"][i]}<br>
Code Iris: ${ci}<br>
APL ${year}: ${df_year["apl"][i].toFixed(1)}<br>
Variation APL/${this.firstYear()}: ${((df_year["apl"][i]-this.years()[this.firstYear()]["apl"][i])*100/this.years()[this.firstYear()]["apl"][i]).toFixed(0)}%<br>
Nb ETP: ${df_year["nb"][i].toFixed(1)}<br>
Population: ${df_year["pop"][i].toFixed(0)}<br>
Population ajustée: ${df_year["pop_ajustee"][i].toFixed(0)}<br>
Population alentour: ${df_year["swpop"][i].toFixed(0)}<br>
APL local: ${df_year["R"][i].toFixed(1)} (${(df_year["R"][i]*100/(df_year["apl"][i]+1e-5)).toFixed(0)}%)`);
	    texts.push(text);
    }
    return texts;
  }

  getGeo() {
    const geo = {
      type: "choropleth",
      locations: this.years()[this.firstYear()]["fid"],
      z: this.years()[this.firstYear()]["apl"],
      zmin: 0,
      //zmax: this.df()["meanws"][0]*2+1,
      zmax: 40,
      hoverinfo: "text",
      text: this.getTexts()[0],
      geojson: this.values()[1],
      featureidkey: "properties.fid",
      colorbar: {title: {text: "APL"}},
      colorscale: [[0.0, "rgb(64,64,127)"],
                    [0.1, "rgb(112,112,127)"],
                    [0.25, "rgb(159,159,127)"],
                    [0.5, "rgb(255,255,127)"],
                    [0.75, "rgb(209,127,79)"],
                    [0.90, "rgb(187,64,55)"],
                    [0.95, "rgb(165,0,32)"],
                    [1.0, "rgb(127,0,0)"]
                  ]
    };
    return geo;
  }

  getSteps(): Plotly.SliderStep[] {
    const steps: Plotly.SliderStep[] = [];
    for (const year of Object.keys(this.years())) {
      const df_year = this.years()[year];
      const step: Plotly.SliderStep = {
        label: String(year),
        value: String(year),
        execute: true,
        visible: true,
        method: 'update',
        args: [
          {
            z: [df_year["apl"], null],
            text: [this.getTexts()[+year - +this.firstYear()], df_year["apl"].map((a, i) => `${a.toFixed(0)}`)],
          }
        ]
      };
      steps.push(step);
    }
    return steps;
  }

  public getSliders(): Partial<Plotly.Slider>[] {
    const sliders: Partial<Plotly.Slider>[] = [{
        active: 0,
        currentvalue: {
          prefix: 'Année: ',
          xanchor: 'right',
        },
        pad: {l: 0, r: 0, t: 0, b: 10},
        len: 0.6,
        x: 0.2,
        y: 0.05,
        steps: this.getSteps(),
      }]
    return sliders;
  }

  getLayout(): Partial<Plotly.Layout> {
    const layout: Partial<Plotly.Layout> = {
      title: {text: this.df()["commune_nom"]},
      geo: {
        projection: { type: 'mercator' },
        center: {lon: this.df()["center_lon"], lat: this.df()["center_lat"] },
        fitbounds: "locations",
        showcoastlines: false,
        showcountries: false,
        showland: false,
        showocean: false,
        showlakes: false,
        showrivers: false,
        showframe: false,
        bgcolor: 'rgb(255,255,255)',
      },
      autosize: true,
      height: 600,
      paper_bgcolor: 'rgb(255,255,255)',
      sliders: this.getSliders(),
    }
    return layout;
  }

  getScatter(): Partial<Plotly.ScatterData> {
    const scatter: Partial<Plotly.ScatterData> = {
      type: 'scattergeo',
      lat: this.years()[this.firstYear()]["lat"],
      lon: this.years()[this.firstYear()]["lon"],
      text: this.years()[this.firstYear()]["apl"].map((a, i) => `${a.toFixed(0)}`),
      mode: 'text',
      textposition: 'middle center',
      textfont: { family: 'Arial', size: 12, color: '#000000' },
      hoverinfo: 'none',
      name: 'APL',
      visible: true,
    };
    return scatter;
  }

  getConfig(): Partial<Plotly.Config> {
    const colors: string[] = ['#ff0000', '#00ff00', '#0000ff'];
    const config: Partial<Plotly.Config> = {
      responsive: true,
      displayModeBar: true,
      displaylogo: false,
      modeBarButtonsToRemove: ['lasso2d', 'toImage'],
      modeBarButtonsToAdd: [
        {
          title: "Hello",
          name: 'color toggler',
          icon: Plotly.Icons.plotlylogo,
          click: function(gd) {
            var newColor = colors[Math.floor(3 * Math.random())];
            (Plotly as any).restyle(gd, 'line.color', newColor);
          }},
        {
          title: "button1",
          name: 'button1',
          icon: Plotly.Icons.pencil,
          click: function(gd) {alert('button1');}
        },
      ],
    }
    return config;
  }
}
