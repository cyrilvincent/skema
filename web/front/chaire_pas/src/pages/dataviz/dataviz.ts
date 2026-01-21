import { Component } from '@angular/core';
import { Searchbox } from './searchbox/searchbox';

@Component({
  selector: 'app-dataviz',
  imports: [ Searchbox],
  templateUrl: './dataviz.html',
  styleUrl: './dataviz.scss',
})
export class Dataviz {

}
