import { Component, computed, input, signal } from '@angular/core';
import { professions } from './dataviz-parameters.data';
import {MatInputModule} from '@angular/material/input';
import {MatSelectModule} from '@angular/material/select';
import {MatFormFieldModule} from '@angular/material/form-field';
import {FormControl, FormsModule, ReactiveFormsModule} from '@angular/forms';
import { Profession } from './dataviz-parameters.interface';
import {MatExpansionModule} from '@angular/material/expansion';
import {MatIconModule} from '@angular/material/icon';

interface Food {
  value: string;
  viewValue: string;
}

@Component({
  selector: 'app-dataviz-parameters',
  imports: [MatFormFieldModule, MatSelectModule, MatInputModule, FormsModule, ReactiveFormsModule, MatExpansionModule, MatIconModule],
  templateUrl: './dataviz-parameters.html',
  styleUrl: './dataviz-parameters.scss',
})
export class DatavizParameters {
  type = input<string>("APL");
  professions = computed(() => professions[this.type()]);
  generaliste = computed(() => this.professions().filter(p => p.id === 10)[0])
  professionControl = new FormControl<Profession | null>(this.generaliste());
  selectedProfession = signal<Profession | null>(this.generaliste());

  constructor() {
    this.professionControl.valueChanges.subscribe(
      p => this.selectedProfession.set(p)
    )
  }


}
