import { ChangeDetectionStrategy, Component, computed, inject, input, output, signal } from '@angular/core';
import {FormControl, FormsModule, ReactiveFormsModule} from '@angular/forms';
import {MatAutocompleteModule} from '@angular/material/autocomplete';
import {MatInputModule} from '@angular/material/input';
import {MatFormFieldModule} from '@angular/material/form-field';
import { SearchService } from './search-service';
import { debounceTime, distinctUntilChanged, map } from 'rxjs';
import {MatIconModule} from '@angular/material/icon';
import {MatTooltipModule} from '@angular/material/tooltip';

@Component({
  selector: 'app-searchbox',
  imports: [FormsModule, MatFormFieldModule, MatInputModule, MatAutocompleteModule, ReactiveFormsModule, MatIconModule, MatTooltipModule],
  templateUrl: './searchbox.html',
  styleUrl: './searchbox.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Searchbox {
  searchControl = new FormControl<[string, string] | null>(null);
  searchService = inject(SearchService);
  options = computed<[string, string][]>(() => this.type() == "APL" ? this.searchService.apl_codes() : this.searchService.sae_codes())
  searchLoading = this.searchService.loading;
  optionSelectedEvent = output<string | null>();
  codes: { [key: string]: string } = {"CC": "Code INSEE", "CD": "Département", "CR": "Région", "CP": "Code postal", "CE": "Communauté de commune", "CA": "Arrondissement de département", "CF": "France"}
  type = input<string>("APL");

  ngOnInit() {
    this.searchService.init();
    this.searchControl.valueChanges.pipe(
      debounceTime(500),
      distinctUntilChanged(),
      map((v) => { 
        if (typeof v === "string") {
          this.optionSelectedEvent.emit(null);
          this.searchService.fetchFind(v, this.type());
        }
      }),
    ).subscribe();
  }

  onSelected(v: [string, string]) {
    if (v == null || v[0] == null || v[0].length <= 3) {
      this.optionSelectedEvent.emit(null);
    }
    else if (v[0][0] === "C" && v[0][2] === "-") {
      this.optionSelectedEvent.emit(v[0]);
    }
    else {
      this.optionSelectedEvent.emit(null);
    }
  }
  
  displayTuple(option: [string, string] | null): string {
    return option == null ? "" : option[1];
  }

  displayCode(code: string): string {
    const c = code.slice(0, 2);
    let s = this.codes[c];
    if (c != "CE" && c != "CA" && c != "CF") {
      const num = code.slice(3);
      s += " " + num;
    }
    return s;
  }
}


