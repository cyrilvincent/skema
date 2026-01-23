import { ChangeDetectionStrategy, Component, computed, input, output, signal } from '@angular/core';
import { specialites } from './dataviz-parameters.data';
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

interface Food {
  value: string;
  viewValue: string;
}

@Component({
  selector: 'app-dataviz-parameters',
  imports: [MatFormFieldModule, MatSelectModule, MatInputModule, FormsModule, ReactiveFormsModule, MatExpansionModule, MatIconModule, MatButtonToggleModule, MatTooltipModule, MatButtonModule, MatSlideToggleModule],
  templateUrl: './dataviz-parameters.html',
  styleUrl: './dataviz-parameters.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DatavizParameters {
  type = input<string>("APL");
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
  okEvent = output<[Specialite, number, number, string, boolean]>();

  ngOnInit() {
    this.specialiteControl = new FormControl<Specialite | null>(this.type() == "APL" ? this.generaliste() : this.specialites()[0]);
    this.selectedSpecialite = signal<Specialite>(this.type() == "APL" ? this.generaliste() : this.specialites()[0]);
    this.specialiteControl.valueChanges.subscribe(
      p => this.selectedSpecialite.set(p!)
    )
    this.timeControl.valueChanges.subscribe(
      t => {
        this.time.set(t!);
        if(t === 30) this.expControl.setValue(-0.12);
        else if(t === 45) this.expControl.setValue(-0.08);
        else this.expControl.setValue(-0.06);
      }
    )
    this.expControl.valueChanges.subscribe(
      e => this.exp.set(e!)
    )
    this.hcControl.valueChanges.subscribe(
      h => this.hc.set(h!)
    )
    this.toggleControl.valueChanges.subscribe(
      b => this.fullScreen.set(b!)
    )
  }

  isBlocked(exp: number): boolean {
    return (this.time() > 30 && exp < -0.08) || (this.time() == 30 && exp > -0.06) || (this.time() > 45 && exp < -0.06);
  }

  buttonClicked(): void {
    console.log("Specialite: "+this.selectedSpecialite().id+" Time: "+this.time()+" exp: "+this.exp()+" heure : "+this.hc()+" fullscreen: "+this.fullScreen());
    this.okEvent.emit([this.selectedSpecialite(), this.time(), this.exp(), this.hc(), this.fullScreen()])
  }

}

