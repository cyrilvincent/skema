import { ChangeDetectionStrategy, Component, computed, effect, inject, input, output, signal, untracked } from '@angular/core';
import { specialites } from '../dataviz.data';
import {MatInputModule} from '@angular/material/input';
import {MatSelectModule} from '@angular/material/select';
import {MatFormFieldModule} from '@angular/material/form-field';
import {FormControl, FormsModule, ReactiveFormsModule} from '@angular/forms';
import { Specialite } from '../dataviz.interfaces';
import {MatExpansionModule} from '@angular/material/expansion';
import {MatIconModule} from '@angular/material/icon';
import {MatButtonToggleModule} from '@angular/material/button-toggle';
import {MatTooltipModule} from '@angular/material/tooltip';
import {MatButtonModule} from '@angular/material/button';
import {MatSlideToggleModule} from '@angular/material/slide-toggle';
import { GeoService } from '../geo-dataviz/geo-service';
import {MatProgressSpinnerModule} from '@angular/material/progress-spinner';

@Component({
  selector: 'app-dataviz-parameters',
  imports: [MatFormFieldModule, MatSelectModule, MatInputModule, FormsModule, ReactiveFormsModule, MatExpansionModule, MatIconModule, MatButtonToggleModule, MatTooltipModule, MatButtonModule, MatSlideToggleModule, MatProgressSpinnerModule],
  templateUrl: './dataviz-parameters.html',
  styleUrl: './dataviz-parameters.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DatavizParameters {
  type = input<string>("APL");
  geoType = signal<string>("iris");
  geoTypeControl = new FormControl<string>("iris");
  code = input<string | null>(null);
  specialites = computed(() => specialites[this.type()]);
  generaliste = computed(() => this.specialites().filter(p => p.id === 10)[0])
  specialiteControl = new FormControl<Specialite | null>(null);
  selectedSpecialite = signal<Specialite>(this.generaliste());
  timeControl = new FormControl<number>(30);
  time = signal<number>(30);
  expControl = new FormControl<number>(-0.12);
  exp = signal<number>(-0.12);
  hcControl = new FormControl<string>("HC");
  hc = signal<string>("HC");
  disabled = input<boolean>(false);
  toggleControl = new FormControl<boolean>(false);
  fullScreen = signal<boolean>(false);
  okEvent = output<[Specialite, number, number, string, boolean, string, string, string | null]>();
  resolution = signal<string>("HD");
  resolutionControl = new FormControl<string>("HD");
  renderType = signal<string>("dataviz");
  renderTypeControl = new FormControl<string>("dataviz");
  geoService = inject(GeoService);
  lastCode = signal<string>("");
  label = input<string | null>(null);

  constructor() {
    effect(() => this.onCodeChanged(this.code()));
  }

  ngOnInit() {
    this.specialiteControl = new FormControl<Specialite | null>(this.type() == "APL" ? this.generaliste() : this.specialites()[0]);
    this.selectedSpecialite = signal<Specialite>(this.type() == "APL" ? this.generaliste() : this.specialites()[0]);
    this.specialiteControl.valueChanges.subscribe(
      p => this.selectedSpecialite.set(p!)
    )
    this.timeControl.valueChanges.subscribe(
      t => {
        this.time.set(t!);
        if (this.type() == "APL") {
          if(t == 30 && this.exp() == -0.04) this.expControl.setValue(-0.12);
          else if(t == 45 && this.exp() <= -0.1) this.expControl.setValue(-0.08);
          else if (t == 60 && this.exp() <= -0.06) this.expControl.setValue(-0.06);
        }
      }
    );
    this.expControl.valueChanges.subscribe(
      e => {if (this.type() == "APL") this.exp.set(e!);}
    );
    this.hcControl.valueChanges.subscribe(
      h => this.hc.set(h!)
    );
    this.toggleControl.valueChanges.subscribe(
      b => this.fullScreen.set(b!)
    );
    this.resolutionControl.valueChanges.subscribe(
      r => {
        this.resolution.set(r!);
        console.log("resolution: "+r!);
      }
    );
    this.renderTypeControl.valueChanges.subscribe(
      r => {
        this.renderType.set(r!);
        if (r == "dataviz") this.toggleControl.enable();
        else this.toggleControl.disable();
      }
    );
    this.geoTypeControl.valueChanges.subscribe(
      g => this.geoType.set(g!)
    )
  }

  onCodeChanged(code: string | null) { // Warning recursive function
    if (code != null && code != this.lastCode()) { // lastCode for prevent infinite loop not necessary
      console.log("CodeChanged "+ code); 
      const c = this.code()!.slice(0, 2);
      if (c == "CF") {
        this.resolutionControl.setValue("LD");
      }
      else if (c == "CR" && this.resolution() == "HD") {
        this.resolutionControl.setValue("MD");
      }
      else if (c != "CF" && c!= "CR" && this.resolution() == "LD") {
        this.resolutionControl.setValue("HD");
      }
      else if (c == "CC" && this.resolution() != "HD") {
        this.resolutionControl.setValue("HD");
      }
      this.lastCode.set(code);
    }
  }

  isResolutionBlocked(res: string): boolean {
    const code = this.code()?.slice(0, 2);
    if (res=="HD") return code == "CF" || code == "CR";
    else if (res=="MD") return code == "CF" || code == "CC";
    return code != "CF" && code != "CR";
  }

  isBlocked(exp: number): boolean {
    return (this.time() > 30 && exp < -0.08) || (this.time() == 30 && exp > -0.06) || (this.time() > 45 && exp < -0.06);
  }

  buttonClicked(): void {
    console.log("Specialite: "+this.selectedSpecialite().id+" Time: "+this.time()+" exp: "+this.exp()+" heure : "+this.hc()+" fullscreen: "+this.fullScreen());
    if (this.renderType() != "dataviz") {
      this.geoService.save({
            code: this.code()!,
            id: this.selectedSpecialite().id, 
            bor: this.selectedSpecialite().shortLabel, 
            time: this.time(),
            exp: this.exp(),
            hc: this.hc(),
            resolution: this.resolution(),
          }, this.type(), this.renderType(), this.geoType());
    }
    else if (this.fullScreen()) {
      const url = window.location.href+"?fullscreen=true&type="+this.type()+"&code="+this.code()+"&specialite="+this.selectedSpecialite().id+"&time="+String(this.time())+"&hc="+this.hc()+"&exp="+String(this.exp())+"&resolution="+this.resolution()+"&label="+encodeURIComponent(this.label()!)
      window.open(url, "_blank");
    }
    else this.okEvent.emit([this.selectedSpecialite(), this.time(), this.exp(), this.hc(), this.fullScreen(), this.resolution(), this.geoType(), this.label()])
  }

  cancelClicked(): void {
    console.log("Cancel")
    this.geoService._loading.set(false);
    this.geoService.init();
  }

}

