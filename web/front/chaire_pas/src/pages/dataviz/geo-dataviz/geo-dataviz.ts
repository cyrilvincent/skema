import { ChangeDetectionStrategy, Component, computed, effect, inject, input, signal } from '@angular/core';
import { PlotlyModule } from 'angular-plotly.js';
import { GeoInputDTO, GeoTupleDTO, GeoDTO, GeoYearDTO } from '../dataviz.interfaces';
import { GeoService } from './geo-service';

@Component({
  selector: 'app-geo-dataviz',
  imports: [PlotlyModule],
  templateUrl: './geo-dataviz.html',
  styleUrl: './geo-dataviz.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
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
  data = computed<any[]>(() =>  this.showLabel() ? [this.getGeo(), this.type()=="APL" ? this.getScatter() as any : this.getScatterGeo() as any] : [this.getGeo()]); 
  visible = computed<boolean>(() => this.df()["center_lon"] != 0 && !this.loading());
  showLabel = signal<boolean>(false);
  normColorBar = signal<boolean>(true);
  marker = signal<number>(1);
  fullscreen = input<boolean | null>(null);

  constructor() {
    effect(() => this.onInputDTOChanged(this.dto()));
    effect(() => this.onValuesChanged(this.values()));
  }

  ngOnInit() {
    this.service.init();
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
    // console.log("OnValuesChanged")
    // console.log(meanws);
  }

  getText(i: number, df_year: GeoYearDTO, year: string): string {
    if(this.type() == "APL") {
      if(this.geoType() == "iris") {
        return `
Commune: ${df_year["nom_commune"][i]}<br>
Nom Iris: ${df_year["nom_iris"][i]}<br>
Code Iris: ${df_year["code_iris"][i]}<br>
APL ${year}: ${df_year["apl"]![i].toFixed(1)}<br>
Variation APL/${this.firstYear()}: ${((df_year["apl"]![i]-this.years()[this.firstYear()]["apl"]![i])*100/(this.years()[this.firstYear()]["apl"]![i]+0.01)).toFixed(0)}%<br>
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
Variation APL/${this.firstYear()}: ${((df_year["apl"]![i]-this.years()[this.firstYear()]["apl"]![i])*100/(this.years()[this.firstYear()]["apl"]![i]+0.01)).toFixed(0)}%<br>
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
Etablissement le + proche:<br> ${df_year["rs"]![i]=="" ? "Aucun" : df_year["rs"]![i]}<br>
Temps d'accès: ${df_year["time_hc"]![i]==60 ? ">60" : df_year["time_hc"]![i].toFixed(0)} min.<br>
Distance: ${df_year["km"]![i]==60 ? ">60" : df_year["km"]![i].toFixed(0)} km<br>
Variation/${this.firstYear()}: ${((df_year["time_hc"]![i]-this.years()[this.firstYear()]["time_hc"]![i])*100/(this.years()[this.firstYear()]["time_hc"]![i]+0.01)).toFixed(0)}%<br>
Population: ${df_year["pop"][i].toFixed(0)}<br>
  `
      }
    else return "TODO"; // TODO Faire commune
  }

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
    if(this.dto()?.bor == "pharma") return 15;
    if(this.dto()?.bor == "ehpad") return 30;
    return 60;
  }

  clip(value: number, min: number, max: number): number {
    if (value < min) return min;
    if (value > max) return max;
    return value;
  }

  getColorscale(): (string | number)[][] {
    const apl = [[0.0, "rgb(64,64,127)"],
                  [0.1, "rgb(112,112,127)"],
                  [0.25, "rgb(159,159,127)"],
                  [0.5, "rgb(255,255,127)"],
                  [0.75, "rgb(209,127,79)"],
                  [0.90, "rgb(187,64,55)"],
                  [0.95, "rgb(165,0,32)"],
                  [1.0, "rgb(127,0,0)"]];
    const meanw = this.df()["meanws"][0]
    const max = this.getZMax();
    let q25 = 0.25;
    let q50 = 0.5;
    let q75 = 0.75;
    if (!this.normColorBar()) {
      q50 = this.clip(meanw / max, 0.25, 0.75);
      q25 = this.clip((meanw / max) / 2, 0.11, 0.5);
      q75 = this.clip(((meanw / max) + 1) / 2, 0.5, 0.89);
    }
    console.log("meanw "+meanw + " " + q50 + " " + max);
    const sae = [[0.0, "rgb(127,0,0)"],
                  [0.1, "rgb(187,64,55)"],
                  [q25, "rgb(209,127,79)"],
                  [q50, "rgb(255,255,127)"],
                  [q75, "rgb(159,159,127)"],
                  [0.90, "rgb(112,112,127)"],
                  [1.0, "rgb(64,64,127)"]];
    if (this.type() == "APL") return apl;
    return sae;
  }

  getColorbarTitle(): string {
    if (this.type() == "APL") {
      if (this.normColorBar()) return "APL";
      return "APL local";
    }
    if (this.normColorBar()) return "Temps de<br>trajet (min.)";
    return "Temps<br>normalisé"
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
      colorbar: {title: {text: this.getColorbarTitle()}}, 
      colorscale: this.getColorscale(),
      marker: {line: {width: this.marker(),}},
    };
    return geo;
  }

  public getSliders(): Partial<Plotly.Slider>[] {
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
      title: {text: "TODO mettre un titre"}, // TODO depuis searchbox, gérer le fullscreen avec un http get
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
      text: this.years()[this.firstYear()][this.type()=="APL" ? "apl" : "time_hc"]!.map((a, i) => `${a.toFixed(0)}`),
      mode: 'text',
      textposition: 'middle center',
      textfont: { family: 'Arial', size: 12, color: '#000000' },
      hoverinfo: 'skip',
      name: 'APL',
      visible: true,
    };
    return scatter;
  }

  getScatterGeo(): Partial<Plotly.ScatterData> { // TODO C'est seulement un mock à modifier
    const scatter: Partial<Plotly.ScatterData> = {
      type: 'scattergeo',
      lat: this.years()[this.firstYear()]["lat"],
      lon: this.years()[this.firstYear()]["lon"],
      mode: 'markers',
      hoverinfo: 'skip', // TODO gérer le hoverinfo
      text: "TODO",          // TODO getTextGeo
      name: 'APL',
      visible: true,     
      marker: {
        color: "#8800ff",
        size: 10,
        opacity: 1,
        line: {
            color:'#99ff99',
            width:2
        },
      }
    };
    return scatter;
  }

  getSteps(): Plotly.SliderStep[] {
    const steps: Plotly.SliderStep[] = [];
    for (const year of Object.keys(this.years())) {
      const df_year = this.years()[year];
      console.log(year);
      df_year["lon"][0] = df_year["lon"][0]+(+year-2020)*0.01; // TODO A enlever, fyi +year = Number(year)
      console.log( df_year["lon"][0]);
      const step: Plotly.SliderStep = {
        label: year, 
        value: year,
        execute: true,
        visible: true,
        method: 'update',
        args: [
          {
            z: [df_year[this.type()=="APL" ? "apl": "time_hc"]],
            text: [this.getTexts()[+year - +this.firstYear()], df_year[this.type()=="APL" ? "apl": "time_hc"]!.map((a, i) => `${a.toFixed(0)}`)],
            lon: [null, df_year["lon"]],
            lat: [null, df_year["lat"]],
            marker: {
              color: "#00ffff",
              //size: df_year["km"],
            }
          }
        ]
      };
      steps.push(step);
    }
    return steps;
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
          click: (() => {
            this.showLabel.set(!this.showLabel()); // Bug peu visible : revient au slider 1, j'ai testé visible mais c'est pareil
          }),
        },
        {
          title: "Normaliser localement - nationalement",
          name: 'Normalize',
          icon: Plotly.Icons.plotlylogo,
          click: (() => this.normColorBar.set(!this.normColorBar())),  // Idem
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
