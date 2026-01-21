import { Component, ElementRef, model, signal, ViewChild } from '@angular/core';
import { MatSlideToggle } from '@angular/material/slide-toggle';
import {FormControl, FormsModule, ReactiveFormsModule} from '@angular/forms';
import {MatAutocompleteModule} from '@angular/material/autocomplete';
import {MatInputModule} from '@angular/material/input';
import {MatFormFieldModule} from '@angular/material/form-field';

@Component({
  selector: 'app-searchbox',
  imports: [MatSlideToggle, FormsModule, MatFormFieldModule, MatInputModule, MatAutocompleteModule, ReactiveFormsModule, ],
  templateUrl: './searchbox.html',
  styleUrl: './searchbox.scss',
})
export class Searchbox {
  @ViewChild('input') input!: ElementRef<HTMLInputElement>;
  myControl = new FormControl('');
  options: string[] = ['One', 'Two', 'Three', 'Four', 'Five'];
  filteredOptions: string[] = this.options.slice();
  text = signal("")

  filter(): void {
    const filterValue = this.input.nativeElement.value.toLowerCase();
    this.filteredOptions = this.options.filter(o => o.toLowerCase().includes(filterValue));
  }

  okButton() {
    this.text.set(this.input.nativeElement.value)
  }
}

 /*
  
import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { debounceTime, distinctUntilChanged, filter, finalize, map, of, switchMap, tap, catchError } from 'rxjs';
import { toSignal } from '@angular/core/rxjs-interop';

import { CityService, City } from './city.service';

@Component({
  selector: 'app-city-autocomplete',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatAutocompleteModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './city-autocomplete.component.html',
})
export class CityAutocompleteComponent {
  // 1) Contrôle de saisie
  cityCtrl = new FormControl<string>('', { nonNullable: true });

  // 2) Etat de chargement exposé en SIGNAL (pour lecture directe dans le template)
  //    (on ne veut plus d'une simple propriété booléenne si on lit dans le template)
  isLoading = signal(false);

  // 3) Ton pipeline RxJS inchangé
  results$ = this.cityCtrl.valueChanges.pipe(
    // 1) anti-bruit : n’émet pas à chaque frappe trop rapide
    debounceTime(300),
    // 2) on travaille avec une chaîne propre
    map(v => (v ?? '').trim()),
    // 3) on évite d’appeler l’API pour 0/1 char
    filter(v => v.length >= 2),
    // 4) n’appelle pas si la valeur n’a pas changé
    distinctUntilChanged(),
    // 5) indicateur de chargement ON
    tap(() => this.isLoading.set(true)),
    // 6) annule la requête précédente si une nouvelle arrive
    switchMap(term =>
      this.cityService.search(term).pipe(
        catchError(() => of<City[]>([])), // ne casse pas l’UI en cas d’erreur
        finalize(() => this.isLoading.set(false)) // indicateur de chargement OFF
      )
    )
  );

  // 4) Conversion Observable -> Signal
  //    => côté HTML tu liras results() au lieu de results$ | async
  results = toSignal<City[]>(this.results$, { initialValue: [] });

  // 5) Affichage d’un objet dans la textbox
  displayCity = (c?: City | string) =>
    typeof c === 'string' ? c : c ? `${c.name}${c.zip ? ' (' + c.zip + ')' : ''}` : '';

  constructor(private readonly cityService: CityService) {}

  onSelected(city: City) {
    console.log('Sélection :', city);
  }
}


<mat-form-field appearance="outline" class="w-100">
  <mat-label>Ville</mat-label>

  <input
    matInput
    type="text"
    [formControl]="cityCtrl"
    [matAutocomplete]="auto"
    autocomplete="off" />

  @if (isLoading()) {
    <mat-progress-spinner matSuffix diameter="16" mode="indeterminate"></mat-progress-spinner>
  }

  <mat-autocomplete
    #auto="matAutocomplete"
    [displayWith]="displayCity"
    (optionSelected)="onSelected($event.option.value)"
    requireSelection
    autoActiveFirstOption>

    @for (c of results(); track c.id) {
      <mat-option [value]="c">
        {{ c.name }} @if (c.zip) { <small>— {{ c.zip }}</small> }
      </mat-option>
    }

    @if (!isLoading() && results().length === 0) {
      <mat-option disabled>Aucun résultat</mat-option>
    }
  </mat-autocomplete>
</mat-form-field>



// city.service.ts
import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';

export interface City {
  id: number;
  name: string;
  zip?: string;
}

@Injectable({ providedIn: 'root' })
export class CityService {
  constructor(private http: HttpClient) {}

  search(term: string) {
    const params = new HttpParams().set('q', term);
    // Retourne Observable<City[]>, mais on ne l’exposera PAS au template
    return this.http.get<City[]>('/api/cities', { params });
  }
}


API Interface : type MyData = [string, string][]

*/
