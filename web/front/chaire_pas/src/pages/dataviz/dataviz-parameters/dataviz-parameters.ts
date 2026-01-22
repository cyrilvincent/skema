import { ChangeDetectionStrategy, Component, computed, input, signal } from '@angular/core';
import { professions } from './dataviz-parameters.data';
import {MatInputModule} from '@angular/material/input';
import {MatSelectModule} from '@angular/material/select';
import {MatFormFieldModule} from '@angular/material/form-field';
import {FormControl, FormsModule, ReactiveFormsModule} from '@angular/forms';
import { Profession } from './dataviz-parameters.interface';
import {MatExpansionModule} from '@angular/material/expansion';
import {MatIconModule} from '@angular/material/icon';
import {MatButtonToggleModule} from '@angular/material/button-toggle';

interface Food {
  value: string;
  viewValue: string;
}

@Component({
  selector: 'app-dataviz-parameters',
  imports: [MatFormFieldModule, MatSelectModule, MatInputModule, FormsModule, ReactiveFormsModule, MatExpansionModule, MatIconModule, MatButtonToggleModule],
  templateUrl: './dataviz-parameters.html',
  styleUrl: './dataviz-parameters.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DatavizParameters {
  type = input<string>("APL");
  professions = computed(() => professions[this.type()]);
  generaliste = computed(() => this.professions().filter(p => p.id === 10)[0])
  professionControl = new FormControl<Profession | null>(this.generaliste());
  selectedProfession = signal<Profession>(this.generaliste());
  timeControl = new FormControl<number>(30);
  time = signal<number>(30);
  expControl = new FormControl<number>(-0.12);
  exp = signal<number>(-0.12);
  hcControl = new FormControl<string>("HC");
  hc = signal<string>("HC");
  disabled = input<boolean>(false);

  constructor() {
    this.professionControl.valueChanges.subscribe(
      p => this.selectedProfession.set(p!)
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
  }

  isBlocked(exp: number): boolean {
    return (this.time() > 30 && exp < -0.08) || (this.time() == 30 && exp > -0.06) || (this.time() > 45 && exp < -0.06);
  }

}

