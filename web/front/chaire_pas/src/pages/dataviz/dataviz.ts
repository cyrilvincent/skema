import { Component, signal } from '@angular/core';
import { Searchbox } from './searchbox/searchbox';
import { DatavizParameters } from "./dataviz-parameters/dataviz-parameters";

@Component({
  selector: 'app-dataviz',
  imports: [Searchbox, DatavizParameters],
  templateUrl: './dataviz.html',
  styleUrl: './dataviz.scss',
})
export class Dataviz {
  selectedCode = signal<string | null>(null);


  optionSelected(code: string | null) {
    this.selectedCode.set(code);
  }

}
