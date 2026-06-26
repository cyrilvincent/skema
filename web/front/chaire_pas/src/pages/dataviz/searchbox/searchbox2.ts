import { ChangeDetectionStrategy, Component, computed, inject, input, output, signal } from '@angular/core';
import {FormControl, FormsModule, ReactiveFormsModule} from '@angular/forms';
import {MatAutocompleteModule} from '@angular/material/autocomplete';
import {MatInputModule} from '@angular/material/input';
import {MatFormFieldModule} from '@angular/material/form-field';
import { SearchService } from './search-service';
import { debounceTime, distinctUntilChanged, map } from 'rxjs';
import {MatIconModule} from '@angular/material/icon';
import {MatTooltipModule} from '@angular/material/tooltip';
import {MatChipInputEvent, MatChipsModule} from '@angular/material/chips';

@Component({
  selector: 'app-searchbox2',
  imports: [FormsModule, MatFormFieldModule, MatInputModule, MatAutocompleteModule, ReactiveFormsModule, MatIconModule, MatTooltipModule, MatChipsModule],
  templateUrl: './searchbox2.html',
  styleUrl: './searchbox2.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Searchbox2 {
  searchControl = new FormControl<[string, string] | null>(null);
  searchService = inject(SearchService);
  options = this.searchService.codes;
  searchLoading = this.searchService.loading;
  optionSelectedEvent = output<[string, string] | null>();
  codes: { [key: string]: string } = {"CC": "Code INSEE", "CD": "Département", "CR": "Région", "CP": "Code postal", "CE": "Communauté de commune", "CA": "Arrondissement de département", "CF": "France"}
  type = input<string>("APL");
  selectedCodes = signal<[string, string][]>([]);
  selectedCodesEvent = output<[string, string][]>();

  ngOnInit() {
    //this.searchService.init();
    this.searchControl.valueChanges.pipe(
      debounceTime(500),
      distinctUntilChanged(),
      map((v) => { 
        if (typeof v === "string") {
          this.optionSelectedEvent.emit(null);
          this.searchService.fetchFind(v); //, this.type());
        }
      }),
    ).subscribe();
  }

  // onSelected(v: [string, string]) {
  //   if (v == null || v[0] == null || v[0].length <= 3) {
  //     this.optionSelectedEvent.emit(null);
  //   }
  //   else if (v[0][0] === "C" && v[0][2] === "-") {
  //     if (this.selectedCodes().length < this.searchService.nbChipMax()) {
  //       this.selectedCodes.update(l => l.some(([code]) => code == v[0]) ? l : [...l, v]);
  //       this.optionSelectedEvent.emit(v);
  //     }
  //   }
  //   else {
  //     this.optionSelectedEvent.emit(null);
  //   }
  // }

  onSelectedCodes(v: [string, string]) {
    if (v[0][0] === "C" && v[0][2] === "-") {
      if (this.selectedCodes().length < this.searchService.nbChipMax()) {
        this.selectedCodes.update(l => l.some(([code]) => code == v[0]) ? l : [...l, v]);
        this.selectedCodesEvent.emit(this.selectedCodes());
      }
    }
  }
  
  displayTuple(option: [string, string] | null): string {
    return option == null ? "" : option[1];
  }

  displayCode(code: string): string {
    const c = code.slice(0, 2);
    let s = this.codes[c];
    if (c == "CF") s += " (très lent)"
    else if (c != "CE" && c != "CA") {
      const num = code.slice(3);
      s += " " + num;
    }
    return s;
  }

  remove(code: string) {
    this.selectedCodes.update(l =>
      l.filter(tuple => tuple[0] != code)
    );
    this.selectedCodesEvent.emit(this.selectedCodes());
  }
}


