import { Component, computed, effect, inject, input, signal } from '@angular/core';
import { PlotlyModule } from 'angular-plotly.js';
import { GeoInputDTO, GeoTupleDTO, GeoDTO, GeoYearDTO } from '../dataviz.interfaces';
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
  config = signal<Partial<Plotly.Config>>(this.getConfig());  // TODO faire getDATA
  data = computed<any[]>(() =>  this.showLabel() ? [this.getGeo(), this.type()=="APL" ? this.getScatterGeo() as any : this.getScatterGeo() as any] : [this.getGeo()]); 
  visible = computed<boolean>(() => this.df()["center_lon"] != 0);
  showLabel = signal<boolean>(false);
  normColorBar = signal<boolean>(true);
  marker = signal<number>(1);
  fullscreen = input<boolean | null>(null);

  constructor() {
    effect(() => this.onInputDTOChanged(this.dto()));
    effect(() => this.onValuesChanged(this.values()));
  }

  ngOnInit() {
    this.showLabel.set(this.type() != "APL");
  }

  onInputDTOChanged(dto: GeoInputDTO | null) {
    if (dto != null) {
      console.log("onInputDTOchanged "+ this.geoType());
      console.log(dto);
      this.service.fetch(dto, this.type(), this.geoType());
    }
  }

  onValuesChanged(v: GeoTupleDTO) {
    const meanws = this.df()["meanws"]
    console.log("OnValuesChanged")
    console.log(meanws);
  }

// Gerer scattergeo

  getText(i: number, df_year: GeoYearDTO, year: string): string {
    if(this.type() == "APL") {
      if(this.geoType() == "iris") {
        return `
  Commune: ${df_year["nom_commune"][i]}<br>
  Nom Iris: ${df_year["nom_iris"][i]}<br>
  Code Iris: ${df_year["code_iris"][i]}<br>
  APL ${year}: ${df_year["apl"]![i].toFixed(1)}<br>
  Variation APL/${this.firstYear()}: ${((df_year["apl"]![i]-this.years()[this.firstYear()]["apl"]![i])*100/this.years()[this.firstYear()]["apl"]![i]+0.01).toFixed(0)}%<br>
  Nb ETP: ${df_year["nb"]![i].toFixed(1)}<br>
  Population: ${df_year["pop"][i].toFixed(0)}<br>
  Population ajustée: ${df_year["pop_ajustee"]![i].toFixed(0)}<br>
  Population alentour: ${df_year["swpop"]![i].toFixed(0)}
  `
      }
      else {
        return `
  Commune: ${df_year["nom_commune"][i]}<br>
  APL ${year}: ${df_year["apl"]![i].toFixed(1)}<br>
  Variation APL/${this.firstYear()}: ${((df_year["apl"]![i]-this.years()[this.firstYear()]["apl"]![i])*100/this.years()[this.firstYear()]["apl"]![i]+0.01).toFixed(0)}%<br>
  Nb ETP: ${df_year["nb"]![i].toFixed(1)}<br>
  Population: ${df_year["pop"][i].toFixed(0)}<br>
  Population ajustée: ${df_year["pop_ajustee"]![i].toFixed(0)}
  `
      }
    }
    if(this.geoType() == "iris") {
        return `
  Commune: ${df_year["nom_commune"][i]}<br>
  Nom Iris: ${df_year["nom_iris"][i]}<br>
  Code Iris: ${df_year["code_iris"][i]}<br>
  KM ${year}: ${df_year["time_hc"]![i].toFixed(1)}<br>  
  Population: ${df_year["pop"][i].toFixed(0)}<br>
  `
      }  // TODO A Améliorer
    else return "TODO";
  }

  // TODO type() à rendre dynamique dans dataviz
  // TODO geo-service à rendre dynamique

  getTexts(): String[][] {
    const texts: string[][] = [];
    for (const year of Object.keys(this.years())) {
      const df_year = this.years()[year];
      let text = df_year["pop"].map((_, i) => this.getText(i, df_year, year));
	    texts.push(text);
    }
    return texts;
  }

  getZMax(): number {
    if(this.type() == "APL") {
      if(this.normColorBar()) return this.df()["meanws"][0]*2+1
      return this.years()[this.firstYear()]["apl_max"]![0]+1
    }
    else return 60; // TODO Gérer 60 et 15
  }

  getGeo() {
    const geo = {
      type: "choropleth",
      locations: this.years()[this.firstYear()]["fid"],
      z: this.years()[this.firstYear()][this.type() == "APL" ? "apl": "time_hc"],
      zmin: 0,
      zmax: this.getZMax(),
      hoverinfo: "text",
      text: this.getTexts()[0],
      geojson: this.values()[1],
      featureidkey: "properties.fid",
      colorbar: {title: {text: this.normColorBar() ? "APL": "APL local"}},  //TODO getColorbarTitle()
      colorscale: [[0.0, "rgb(64,64,127)"],  // TODO Inverser la colorbar pour SAE
                    [0.1, "rgb(112,112,127)"],  // TODO mettre meanw pour SAE
                    [0.25, "rgb(159,159,127)"],
                    [0.5, "rgb(255,255,127)"],
                    [0.75, "rgb(209,127,79)"],
                    [0.90, "rgb(187,64,55)"],
                    [0.95, "rgb(165,0,32)"],
                    [1.0, "rgb(127,0,0)"]
                  ],
      marker: {line: {width: this.marker(),}},
    };
    return geo;
  }

  getSteps(): Plotly.SliderStep[] {
    const steps: Plotly.SliderStep[] = [];
    for (const year of Object.keys(this.years())) {
      const df_year = this.years()[year];
      df_year["lon"][0] = df_year["lon"][0]+(Number(year)-2020)*0.01; // TODO A enlever
      const step: Plotly.SliderStep = {
        label: String(year),
        value: String(year),
        execute: true,
        visible: true,
        method: 'update',
        args: [
          {
            z: [df_year[this.type()=="APL" ? "apl": "time_hc"], null],
            text: [this.getTexts()[+year - +this.firstYear()], df_year[this.type()=="APL" ? "apl": "time_hc"]!.map((a, i) => `${a.toFixed(0)}`)],
            lon: [null, df_year["lon"]],
            lat: [null, df_year["lat"]],
            marker: {
              color: "#00ffff",
              size: df_year["km"],
            }
          }
        ]
      };
      steps.push(step);
    }
    return steps;
  }

  public getSliders(): Partial<Plotly.Slider>[] { // TODO en fullscreen apparait tj en APL
    const sliders: Partial<Plotly.Slider>[] = [{
        active: 0,
        currentvalue: {
          prefix: 'Année: ',
          xanchor: 'left',
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
      title: {text: "TODO mettre un titre"},
      geo: {
        projection: { type: 'mercator', scale: 2, },
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
      height: this.fullscreen() ? undefined : 600,
      //width: 1200,
      margin: {l: 10, r: 10, t: 30, b: 20},
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
      text: this.years()[this.firstYear()][this.type()=="APL"?"apl":"time_hc"]!.map((a, i) => `${a.toFixed(0)}`),
      mode: 'text',
      textposition: 'middle center',
      textfont: { family: 'Arial', size: 12, color: '#000000' },
      hoverinfo: 'none',
      name: 'APL',
      visible: true,
    };
    return scatter;
  }

  getScatterGeo(): Partial<Plotly.ScatterData> {
    const scatter: Partial<Plotly.ScatterData> = {
      type: 'scattergeo',
      lat: this.years()[this.firstYear()]["lat"],
      lon: this.years()[this.firstYear()]["lon"],
      mode: 'markers',
      hoverinfo: 'none',
      name: 'APL',
      visible: true,
      marker: {
        color: "#00ff00",
        size: 10,
      }
    };
    return scatter;
  }

  getConfig(): Partial<Plotly.Config> {
    const config: Partial<Plotly.Config> = {
      autosizable: true,
      responsive: true,
      displayModeBar: true,
      displaylogo: false,
      locale: 'fr',
      modeBarButtonsToRemove: ['lasso2d', 'select2d', 'toImage'],
      modeBarButtonsToAdd: [
        {
          title: "Afficher les labels",
          name: 'Show labels',
          icon: Plotly.Icons.zoombox,
          click: (() => this.showLabel.set(!this.showLabel())),
        },
        {
          title: "Normaliser localement - nationalement",
          name: 'Normalize',
          icon: Plotly.Icons.plotlylogo,
          click: (() => this.normColorBar.set(!this.normColorBar())),
        },
        {
          title: "Contours",
          name: 'Contours',
          icon: Plotly.Icons.drawline,
          click: (() => this.marker.set(this.marker() == 1 ? 0 : 1)),
        },
      ],
    }
    return config;
  }
}
