import { ChangeDetectionStrategy, Component, computed, effect, ElementRef, inject, input, OnInit, signal, ViewChild } from '@angular/core';
import { PlotlyModule, PlotlyComponent, PlotlyService } from 'angular-plotly.js';
import { GeoInputDTO, GeoTupleDTO, GeoDTO, GeoYearDTO, EtabDTO } from '../dataviz.interfaces';
import { GeoService } from './geo-service';
import { specialites } from '../dataviz.data';
//import Plotly from 'plotly.js-dist-min'

@Component({
  selector: 'app-geo-dataviz',
  imports: [PlotlyModule],  // [PlotlyComponent] for lazy load
  //providers: [PlotlyService] For Lazy load
  templateUrl: './geo-dataviz.html',
  styleUrl: './geo-dataviz.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class GeoDataviz implements OnInit {
  plotlyReady = signal(true); // false for lazy loading
  service = inject(GeoService);
  values = this.service.geoTupleDTO;
  loading = this.service.loading;
  dto = input<GeoInputDTO | null>(null);
  type = input<string>("APL");
  geoType = input<string>("iris");
  df = computed<GeoDTO>(() => this.values()[0]);
  years = computed<{[key: string]: GeoYearDTO}>(() =>  this.df()["years"]);
  firstYear = computed<string>(() => this.dto() && this.dto()?.code == "CF-00" ? "2020" : Object.keys(this.years())[0]);
  sliderYear = signal<string>(this.firstYear());
  layout = computed<Partial<Plotly.Layout>>(() => this.getLayout()); 
  config = signal<Partial<Plotly.Config>>(this.getConfig()); //({}); for lazy loading gituhub 22/02/2026
  //data = computed<any[]>(() =>  this.showLabel() ? [this.getGeo(), this.type()=="APL" ? this.getScatter() as any : this.getScatterGeo() as any] : [this.getGeo()]); 
  data = computed<any[]>(() => this.getData());
  visible = computed<boolean>(() => this.df()["center_lon"] != 0 && !this.loading());
  showLabel = signal<boolean>(false);
  normColorBar = signal<boolean>(true);
  marker = signal<number>(1);
  fullscreen = input<boolean | null>(null);
  label = input<string | null>(null);
  frames = computed<Partial<Plotly.Frame>[]>(() => this.getFrames());
  mapType = signal<string>("choropleth");
  zooms: { [key: string]: number } = {"CC": 11, "CP": 11, "CA": 8, "CE": 8, "CD": 7, "CR": 6, "CF": 4};
  @ViewChild('myPlot') plotEl!: ElementRef;
  sae2 = input<boolean>(false);
  specialites = computed(() => this.sae2() ? specialites["SAE2"] : specialites[this.type()]);
  isPlaying = signal(false);
  animInterval: any = null;
  currentStep = signal(0);
  //Plotly: any = null; for lazy loading

  constructor() {
    effect(() => this.onInputDTOChanged(this.dto()));
    //effect(() => this.onValuesChanged(this.values()));
  }

  async ngOnInit() {
    this.service.init();
    this.showLabel.set(this.type() != "APL");

    // For lazy load, uniquement quand on sera en prod sur un nginx, car ca declenche une erreur sur cyrilvincent.com
    //this.Plotly = await import('plotly.js-dist-min');
    // PlotlyService.setPlotly(this.Plotly.default);
    // console.log("Plotly lazy loaded");
    // console.log(this.Plotly);
    // this.config.set(this.getConfig());
    // this.plotlyReady.set(true);
  }

  getData(): any[] {
    if (this.showLabel()) {
      if (this.type() == "APL") return [this.getGeo(), this.getScatter() as any]
      // if (this.mapType() == "choropleth") return [this.getGeo(), this.getScatterGeo() as any]
      // return [this.getGeo(), this.getScatterGeo(2) as any, this.getScatterGeo() as any]
      return [this.getGeo(), this.getScatterGeo() as any]
    }
    return [this.getGeo()];
  }

  // autoPlay() {
  //   //         (animated)="autoPlay()"
  //   //    (sliderChange)="onSliderChange($event)"
  //   // const el = this.plotEl.nativeElement.querySelector('.js-plotly-plot');
  //   // const frames = el._transitionData._frames;
  //   // const activeStep = el._fullLayout.sliders[0].active;
  //   // const lastIndex = frames.length - 1;
  //   // const active = (el as any).layout.updatemenus[0].active
  //   // if (activeStep === lastIndex && active <= 1) {
  //   //   const buttons = this.plotEl.nativeElement.querySelectorAll('.updatemenu-button');
  //   //   setTimeout(() => buttons[active]?.dispatchEvent(new MouseEvent('click', { bubbles: true })), active == 0 ? 1000 : 400);
  //   // }
  // }

  // onSliderChange(event: any) {
  //   // this.sliderYear.set(event.step.label);
  //   // console.log("Slider "+this.sliderYear())
  // }

  onSliderClicked(event: any) {
    if (event.active == 0) {
      console.log("Play")
      this.pause();
      this.play(1000);
    }
    else if (event.active == 1) {
      console.log("FastForward")
      this.pause();
      this.play(400)
    }
    else if (event.active == 2) {
      console.log("Pause")
      this.pause()
    }
  }

  play(interval: number) {
    const el = this.plotEl.nativeElement.querySelector('.js-plotly-plot');
    this.animInterval = setInterval(() => {
      const step = this.currentStep();
      if (step >= this.frames().length) {
        this.currentStep.set(0);
        return;
      }
      Plotly.animate(el, [this.frames()[step].name!], {
        mode: 'immediate',
        frame: { duration: 0, redraw: true },
        transition: { duration: interval / 10 }
      });
      this.currentStep.update(s => s + 1);
    }, interval);
    this.isPlaying.set(true);
  }

  pause() {
    if (this.isPlaying()) {
      clearInterval(this.animInterval);
      this.animInterval = null;
      this.isPlaying.set(false);
    }
  }

  onInputDTOChanged(dto: GeoInputDTO | null) {
    if (dto != null) {
      console.log("onInputDTOchanged "+ this.geoType());
      console.log(dto);
      this.service.fetch(dto, this.type(), this.geoType());
      this.sliderYear.set(this.firstYear());
    }
  }

  // onValuesChanged(v: GeoTupleDTO) {
  //   const meanws = this.df()["meanws"]
  // }

  variation(a: number, b: number, delta=1): string {
    let result = ((a - b) * 100 / (b + 0.01)).toFixed(delta);
    if (a > b) result = "+" + result;
    return result;
  }

  difference(a: number, b: number, delta=1): string {
    let result = (a - b).toFixed(delta);
    if (a > b) result = "+" + result;
    return result;
  }

  getCommuneIrisText(i: number, df_year: GeoYearDTO): string {
    return `<b>${df_year["nom_commune"][i]} - ${df_year["nom_iris"][i]} (${df_year["code_iris"][i]})</b><br><br>`;
  }

  getCommuneText(i: number, df_year: GeoYearDTO): string {
    return `<b>${df_year["nom_commune"][i]}</b><br><br>`;
  }

  getAplText(i: number, df_year: GeoYearDTO, year: string): string {
    let s = "<b>Accessibilité aux soins</b><br>";
    s += `APL ${year}: ${df_year["apl"]![i].toFixed(1)}<br>`;
    //s += `(Δ${this.firstYear()} ${this.variation(df_year["apl"]![i], this.years()[this.firstYear()]["apl"]![i])}%)<br>`
    s += `  Δ à la moyenne nationale: ${this.variation(df_year["apl"]![i], this.df()["meanws"][+year-(+this.firstYear())])}%<br>`
    s += `  Δ 2020: ${this.variation(df_year["apl"]![i], this.df()["years"]["2020"]["apl"]![i])}%<br>`
    s += `Nb ETP: ${df_year["nb"]![i].toFixed(1)}<br><br>`
    return s;
  }

  getPopText(i: number, df_year: GeoYearDTO): string {
    let s = "<b>Caractéristiques Socio-économiques</b><br>";
    s += `Population: ${df_year["pop"][i].toFixed(0)}`
    //if ("pop_ajustee" in df_year) s += ` (ajustée: ${df_year["pop_ajustee"]![i].toFixed(0)})`;
    if (df_year["pop65p"]![i] != 0) {
      s += `<br>Proportion de +65 ans: ${(df_year["pop65p"]![i]*100/(df_year["pop"]![i]+0.01)).toFixed(1)}%<br>`;
      //s += `(Δ${this.firstYear()} ${this.variation(df_year["pop65p"]![i], this.years()[this.firstYear()]["pop65p"]![i])}%)<br>`;
      s += `  Δ à la moyenne nationale de ${((df_year["pop_year"]![i]+2000))}: ${this.difference(df_year["pop65p"]![i]*100/(df_year["pop"]![i]+0.01), df_year["pop65p_ratio_france"]![i]*100)}pp`;
    }
    return s;
  }

  getFiloText(i: number, df_year: GeoYearDTO): string {
    let s = "<br>Taux de pauvreté: ";
    if (df_year["tp60"]![i] == 0) s+= "N/A<br>"
    else {
      s += `${df_year["tp60"]![i].toFixed(1)}%<br>`;
      //s += `(Δ${this.firstYear()} ${this.variation(df_year["tp60"]![i], this.years()[this.firstYear()]["tp60"]![i])}%)<br>`
      s += `  Δ à la moyenne nationale de ${((df_year["filo_year"]![i]+2000))}:  ${this.difference(df_year["tp60"]![i], df_year["tp60_france"]![i])}pp<br>`;
    }
    s += "Revenu médian: ";
    if (df_year["med"]![i] == 0) s+= "N/A<br>"
    else {
      s += `${df_year["med"]![i].toFixed(0)}€<br>`;
      //s += `(Δ${this.firstYear()} ${this.variation(df_year["med"]![i], this.years()[this.firstYear()]["med"]![i])}%)<br>`;
      s += `  Δ à la moyenne nationale de ${((df_year["filo_year"]![i]+2000))}: ${this.variation(df_year["med"]![i],df_year["med_france"]![i])}%<br>`;
    }
    s += "Indice de Gini: ";
    if (df_year["med"]![i] == 0) s+= "N/A<br>"
    else {
      s += `${(df_year["gi"]![i]*100).toFixed(1)}%<br>`;
      //s += `(Δ${this.firstYear()} ${this.variation(df_year["gi"]![i], this.years()[this.firstYear()]["gi"]![i])}%)<br>`;
      s += `  Δ à la moyenne nationale de ${((df_year["filo_year"]![i]+2000))}: ${this.difference(df_year["gi"]![i] * 100, df_year["gi_france"]![i] * 100)}pp<br>`;
    }
    return s;
  }

  getEtablissementText(i: number, df_year: GeoYearDTO, year: string): string {
    let s = "<b>Aucun établissement à moins de 60 min</b><br>";
    if (df_year["rs"]![i]!="") {
      s = `<b>Etablissement le + proche:</b><br>${df_year["rs"]![i]}<br>`
      s += `Temps d'accès: ${df_year["time_hc"]![i]==60 ? ">60" : df_year["time_hc"]![i].toFixed(0)} min<br>`
      //s += `(Δ${this.firstYear()} ${this.variation(df_year["time_hc"]![i], this.years()[this.firstYear()]["time_hc"]![i])}%)<br>`
      s += `  Δ à la moyenne nationale: ${this.variation(df_year["time_hc"]![i], this.df()["meanws"][+year-(+this.firstYear())])}%<br>`;
      s += `Distance: ${df_year["km"]![i]==60 ? ">60" : df_year["km"]![i].toFixed(0)} km<br><br>`
      //s += `(Δ${this.firstYear()} ${this.variation(df_year["km"]![i], this.years()[this.firstYear()]["km"]![i])}%)<br><br>`
    }
    return s;
  }

  getAplTexts(i: number, df_year: GeoYearDTO, year: string, isIris: boolean): string {
    let s = isIris ? this.getCommuneIrisText(i, df_year) : this.getCommuneText(i, df_year);
    s += this.getAplText(i, df_year, year);
    //if (isIris) {
      s += this.getPopText(i, df_year);
      s += this.getFiloText(i, df_year);
    //}
    return s
  }

  getSaeTexts(i: number, df_year: GeoYearDTO, year: string, isIris: boolean): string {
    let s = isIris ? this.getCommuneIrisText(i, df_year) : this.getCommuneText(i, df_year);
    s += this.getEtablissementText(i, df_year, year);
    //if (isIris) {
      s += this.getPopText(i, df_year);
      s += this.getFiloText(i, df_year);
    //}
    return s
  }

  getText(i: number, df_year: GeoYearDTO, year: string): string {
    if(this.type() == "APL") {
      if(this.geoType() == "iris") return this.getAplTexts(i, df_year, year, true);
      else return this.getAplTexts(i, df_year, year, false);
    }
    if(this.geoType() == "iris") return this.getSaeTexts(i, df_year, year, true);
    else return this.getSaeTexts(i, df_year, year, false);
  }

  getTexts(): string[][] {
    const texts: string[][] = [];
    if (this.dto()?.code == "CF") return texts;
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
    if(this.dto()?.id == 4) return 15;
    if(this.dto()?.id == 5) return 30;
    return 60;
  }

  getZMin(): number {
    if(this.type() == "APL" && !this.normColorBar())
      return this.years()[this.firstYear()]["apl_min"]![0]
    return 0
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
    if (this.normColorBar()) return "Trajet<br>(min.)";
    return "Temps<br>normalisé"
  }

  getGeo() {
    const geo = {
      type: this.mapType(),
      locations: this.years()[this.sliderYear()]["fid"],
      z: this.years()[this.sliderYear()][this.type() == "APL" ? "apl": "time_hc"],
      zmin: this.getZMin(),
      zmax: this.getZMax(),
      //hoverinfo: "text",
      hoverinfo: this.type() == "APL" || (this.years()[this.sliderYear()].etab!["lon"].length < 40) || !this.showLabel() ? "text" : "skip",
      text: this.getTexts()[0],
      geojson: this.values()[1],
      featureidkey: "properties.fid",
      colorbar: {
        title: {text: this.getColorbarTitle()},
        side: "left",
        padding: { t: 0, r: 20, b: 0, l: 0 },
      }, 
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

  getTitle(): string {
    const codes: { [key: string]: string } = {"CC": "Commune de", "CD": "Département", "CR": "Région", "CP": "Commune(s) de", "CE": "Communauté de commune", "CA": "Arrondissement de département", "CF": "France"};
    if(this.dto() != null) {
      const code = this.dto()!.code.slice(0, 2);
      let s = this.specialites().find(s => s.id == this.dto()!.id)!.label + "<br>";
      s += codes[code];
      if (code != "CF") s += " "+this.label();
      return s;
    }
    return "";
  }

  getZoom(): number {
    const code: string = this.dto()!.code.slice(0,2)
    return this.zooms[code];
  }

  getLayout(): Partial<Plotly.Layout> {
    const layout: Partial<Plotly.Layout> = {
      title: {text: this.getTitle()},
      geo: {
        projection: { type: 'mercator', scale: 1, },
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
      map: {
        style: 'open-street-map',
        center: {lon: this.df()["center_lon"], lat: this.df()["center_lat"] },
        zoom: this.getZoom(),
      },
      autosize: true,
      height: this.fullscreen() ? window.innerHeight * 0.98 : 500,
      //width: 1200,
      margin: {l: 10, r: 120, t: 80, b: 20},
      paper_bgcolor: 'rgb(255,255,255)',
      sliders: this.getSliders(),
      updatemenus: [{
        type: 'buttons',
        showactive: true,
        direction: 'left',
        x: 0.1,
        y: 0.05,
        xanchor: 'right',
        yanchor: 'top',
        buttons: [
          {
            label: '▶',
            method: "skip",
            args: [],
            //method: 'animate',
            // args: [
            //   null,
            //   {
            //     // fromcurrent: true,
            //     // mode: 'immediate',
            //     // transition: { duration: 300, easing: 'linear' },
            //     // frame: { duration: 1000, redraw: true },
            //   },
            // ],
          },
          {
            label: '⏭',
            method: "skip",
            args: [],
            // method: 'animate',
            // args: [
            //   null,
            //   {
            //     fromcurrent: true,
            //     mode: 'immediate',
            //     transition: { duration: 300, easing: 'linear' },
            //     frame: { duration: 200, redraw: true },
            //   },
            // ],
          },
          {
            label: '⏸',
            method: "skip",
            args: [],
            // method: 'animate',
            // args: [
            //   [null],
            //   { mode: 'immediate',} //frame: { duration: 0, redraw: true } },
            // ],
          },
        ],
      }]
    }
    return layout;
  }

  getScatter(): Partial<Plotly.ScatterData> {
    const scatter: Partial<Plotly.ScatterData> = {
      type: 'scattergeo',
      lat: this.years()[this.sliderYear()]["lat"],
      lon: this.years()[this.sliderYear()]["lon"],
      text: this.years()[this.sliderYear()][this.type()=="APL" ? "apl" : "time_hc"]!.map((a, i) => `${a.toFixed(0)}`),
      mode: 'text',
      textposition: 'middle center',
      textfont: { family: 'Arial', size: 12, color: '#000000' },
      hoverinfo: 'skip',
      name: 'APL',
      visible: true,
    };
    return scatter;
  }

  getScatterSize(passus: number[], enlarge=0): number[] {
    if(this.dto() != null) {
      if (this.dto()!.id == 5) return passus.map(_ => 7);
      if (this.dto()!.id == 4) return passus.map(_ => 3);
      let coef = 0;
      let c = 2;
      if (this.dto()!.id <= 2) coef = 8/30000;
      else if (this.dto()!.id == 3) coef = 6/100;
      if (this.dto()!.id <= 3) c=3;
      return passus.map(p => p<0 ? c : c+p*coef+enlarge)
    }
    return [];
  }

  getTensionScatterColor(tensions: number[], enlarge=0): string[] {
    if(this.dto() != null) {
      return tensions.map(t => {
        let r = 127;
        let g = 127;
        let b = 0
        if (t != -1 && enlarge == 0) {
          let a = 0.1;
          let b = 3000;
          if (this.dto()!.id > 2) {
            a = 10;
            b = 11;
          }
          r = this.clip(Math.round((t-b)*a+127.5), 0, 255);
          g = 255 - this.clip(Math.round((t-b)*a+127.5), 0, 255);
        }
        else r = g = b = 127;
        return `rgb(${r},${g},${b},255)`;
      })
    }
    return [];
  }

  getEhpadPharmaScatterColor(p1: number[] | undefined, p1_mean: number[] | undefined, enlarge=0): string[] {
    if(this.dto() != null) {
      let i = 0;
      if (p1) {
        const mean = p1_mean!.find(p => p > 0);
        return p1.map(p => {
          if (p == -1 || !mean || mean < 0 || enlarge != 0 || this.dto()!.id == 4) return "rgb(127,127,127,255)";
          let r = 127;
          let g = 127;
          if (p != -1) {
            const ratio = p / mean;
            r = this.clip(Math.round(127.5 * ratio), 0, 255);
            g = 255 - r;
          }
          i++;
          const rgb = `rgb(${r},${g},0,255)`;
          return rgb;
        })
      }
      return [];
    }
    return [];
  }



  getScatterGeoText(i: number, etab: EtabDTO, year: string): string {
    let s = etab["rs"][i];
    if (this.dto()!.id <= 3) {
      s += "<br>";
      s += `NB passage ${etab["year"][i]}: ${etab["passu"][i] < 0 || etab["passu"][i] == null ? "N/A" : etab["passu"][i]}<br>`;
      s += `ETP: ${etab["etp"][i] < 0 ? "N/A" : etab["etp"][i].toFixed(1)}<br>`
      s += `Dont salarié: ${etab["etpsal"][i] < 0 ? "N/A" : etab["etpsal"][i].toFixed(1)}<br>`
      s += `Dont libéraux: ${etab["efflib"][i] < 0 ? "N/A" : etab["efflib"][i].toFixed(1)}<br>`
      s += `Tension: ${etab["tension"][i] < 0 ? "N/A" : etab["tension"][i].toFixed(0)} passage/ETP`
    }
    else if (this.dto()!.id == 5) {
      s += "<br>";
      if (etab["p1"]) {
        const p1 = etab["p1"]![i];
        if (!p1 || p1 < 0) s+= "Prix en chambre seule: N/A";
        else {
          s += `Prix en chambre seule: ${p1.toFixed(0)}€<br>`;
          s += `  Δ à la moyenne nationale: ${this.variation(p1, etab["p1_mean"]![i])}%<br>`;
          const etab20 = this.years()["2020"]["etab"]!
          const i20 = etab20["fi"].indexOf(etab["fi"][i])
          if (i20 >= 0 && etab20["p1"]) {
            const p120 = etab20["p1"]![i20]
            s += `  Δ 2020: ${p120 < 0 ? "N/A" : this.variation(p1, p120)}%`
          }
        }
      }
    }
    return s;
  }

  getScatterGeoTexts(year: string): string[] {
    const df_year = this.years()[year];
    const etab = df_year["etab"]!;
    const s = etab["rs"].map((_, i) => this.getScatterGeoText(i, etab, year))
    return s;
  }

  getScatterGeo(enlarge=0): Partial<Plotly.ScatterData> {
    const etab = this.years()[this.sliderYear()]["etab"]!;
    const scatter: Partial<Plotly.ScatterData> = {
      //type: 'scattergeo',
      type: this.mapType() == "choropleth" ? "scattergeo" : "scattermap",
      lat: etab["lat"],
      lon: etab["lon"],
      mode: 'markers',
      //hoverinfo: etab["lon"].length < 20 ? "text": "skip",
      hoverinfo: "text",
      text: this.getScatterGeoTexts(this.sliderYear()),
      name: 'APL',
      visible: true,     
      marker: {
        color: ![4, 5].includes(this.dto()!.id) ? 
               this.getTensionScatterColor(etab["tension"], enlarge) : 
               this.getEhpadPharmaScatterColor(etab["p1"], etab["p1_mean"], enlarge),
        size: this.getScatterSize(etab["passu"], enlarge),
        opacity: 1,
        //symbol: 'circle-stroked',
        line: {
          color: 'white',
          width: 1
        }
        
        // opacity: 1,
      }
    };
    return scatter;
  }

  // getSteps(): Plotly.SliderStep[] {
  //   const steps: Plotly.SliderStep[] = [];
  //   for (const year of Object.keys(this.years())) {
  //     if (+year < 2020 && this.dto()?.code == "CF-00") continue;
  //     const df_year = this.years()[year];
  //     const etab = this.years()[year]["etab"]!;
  //     const step: Plotly.SliderStep = {
  //       label: year, 
  //       value: year,
  //       execute: true,
  //       visible: true,
  //       method: 'update',
  //       args: [
  //         {
  //           z: [df_year[this.type()=="APL" ? "apl": "time_hc"]],
  //           text: [this.getTexts()[+year - +this.firstYear()], this.type() == "APL" ? df_year["apl"]!.map((a, i) => `${a.toFixed(0)}`) : this.getScatterGeoText(etab)],
  //           lon: [null, this.type() == "APL" ? df_year["lon"] : etab["lon"]],
  //           lat: [null, this.type() == "APL" ? df_year["lat"] : etab["lat"]],
  //           marker: {
  //             color: this.type() == "APL" ? undefined : this.getScatterColor(etab["tension"]),
  //             size: this.type() == "APL" ? undefined : this.getScatterSize(etab["passu"])
  //           }
  //         }
  //       ]
  //     };
  //     steps.push(step);
  //   }
  //   return steps;
  // }

  getSteps(): Plotly.SliderStep[] {
    return Object.keys(this.years())
      .filter(year => !(+year < 2020 && this.dto()?.code == "CF-00"))
      .map(year => ({
        label: year,
        value: year,
        execute: true,
        visible: true,
        method: 'animate',
        args: [
          [year],
          {
            mode: 'immediate',
            transition: { duration: 100, easing: 'linear' },
            frame: { duration: 100, redraw: true },
          },
        ],
      }));
  }

  getFrames(): Partial<Plotly.Frame>[] {
    const frames: Partial<Plotly.Frame>[] = [];
    for (const year of Object.keys(this.years())) {
      if (+year < 2020 && this.dto()?.code == "CF-00") continue;
      const df_year = this.years()[year];
      const etab = this.years()[year]["etab"]!;
      const frame: Partial<Plotly.Frame> = {
        name: year,
        data: [
          {
            z: df_year[this.type() == "APL" ? "apl" : "time_hc"],
            text: this.getTexts()[+year - +this.firstYear()],
          },
          {
            text: this.type() == "APL" ? df_year["apl"]!.map(a => `${a.toFixed(0)}`) : this.getScatterGeoTexts(year),
            lon: this.type() == "APL" ? df_year["lon"] : etab["lon"],
            lat: this.type() == "APL" ? df_year["lat"] : etab["lat"],
            marker: {
              color: this.type() == "APL" ? undefined : (![4, 5].includes(this.dto()!.id) ? 
                                                         this.getTensionScatterColor(etab["tension"]) : 
                                                         this.getEhpadPharmaScatterColor(etab["p1"], etab["p1_mean"])),
              size: this.type() == "APL" ? undefined : this.getScatterSize(etab["passu"]),
            },
          },
        ],
      };
      frames.push(frame);
    }
    return frames;
  }

  getConfig(): Partial<Plotly.Config> {
    const config: Partial<Plotly.Config> = {
      autosizable: true,
      responsive: true,
      displayModeBar: true,
      displaylogo: false,
      locale: 'fr',
      modeBarButtonsToRemove: ['lasso2d', 'select2d'],  //, 'toImage'],
      modeBarButtonsToAdd: [
        {
          title: "Afficher les labels",
          name: 'Show labels',
          icon: Plotly.Icons.drawline,  // Prefixer par this si lazy
          click: (async () => {
            this.service._loading.set(true);
            this.showLabel.set(!this.showLabel());
            this.service._loading.set(false);
          }),
        },
        {
          title: "Normaliser localement - nationalement",
          name: 'Normalize',
          icon: Plotly.Icons.zoombox,
          click: (() => this.normColorBar.set(!this.normColorBar())),  // Idem
        },
        {
          title: "Contours",
          name: 'Contours',
          icon: Plotly.Icons.plotlylogo,
          click: (() => {
            this.service._loading.set(true);
            this.marker.set(this.marker() == 1 ? 0 : 1)
            this.service._loading.set(false);
          }),
        },
        {
          title: "Map",
          name: 'map',
          icon: Plotly.Icons.drawrect,
          click: (() => {
            this.service._loading.set(true);
            this.mapType.set(this.mapType() == "choropleth" ? "choroplethmap": "choropleth");
            this.service._loading.set(false);
          }),
        }
      ],
    }
    return config;
  }
}
