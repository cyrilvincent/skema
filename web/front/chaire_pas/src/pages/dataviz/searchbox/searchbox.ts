import { Component, ElementRef, inject, model, signal, ViewChild } from '@angular/core';
import { MatSlideToggle } from '@angular/material/slide-toggle';
import {FormControl, FormsModule, ReactiveFormsModule} from '@angular/forms';
import {MatAutocompleteModule} from '@angular/material/autocomplete';
import {MatInputModule} from '@angular/material/input';
import {MatFormFieldModule} from '@angular/material/form-field';
import { SearchService } from './search-service';
import { debounceTime, distinctUntilChanged, map, tap } from 'rxjs';

@Component({
  selector: 'app-searchbox',
  imports: [MatSlideToggle, FormsModule, MatFormFieldModule, MatInputModule, MatAutocompleteModule, ReactiveFormsModule, ],
  templateUrl: './searchbox.html',
  styleUrl: './searchbox.scss',
})
export class Searchbox {
  @ViewChild('input') input!: ElementRef<HTMLInputElement>;
  myControl = new FormControl<[string, string] | null>(null); // TODO Renommer
  searchService = inject(SearchService)
  options = this.searchService.codes;
  text = signal<string>("")
  loading = this.searchService.loading;

  // Côté back, si 2 labels sont identiques virer celui qui n'est pas CC

  constructor() {
    this.myControl.valueChanges.pipe(
      debounceTime(500),
      distinctUntilChanged(),
      map((v) => console.log("Map "+v)),
      tap(() => {
        console.log("ValueChanged " + this.input.nativeElement.value); // TODO passer au map sur v[1]
        this.searchService.fetchFind(this.input.nativeElement.value);
        }),
    ).subscribe();
  }

  okButton() {
    this.text.set(this.myControl.value ? this.myControl.value[0] : "Nothing");
  }


  onSelected(tuple: [string, string]) {
    console.log('ID sélectionné =', tuple[0], ' | Label =', tuple[1]);
  }
  
  displayTuple(option: [string, string]): string {
    return option[1];
  }

  get selectedId(): string | null {
      const v = this.myControl.value;
      console.log("selectedId "+v);
      if (v == null || v[0] == null) {
        return null;
      }
      if (v[0].length <= 3) {
        return null;
      }
      if (v[0][0] == "C" && v[0][2] == "-") {
        return v[0];
      }
      return null;
    }
}


