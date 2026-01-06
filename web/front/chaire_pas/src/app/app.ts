import { Component, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { About } from "../about/about";
import { DatavizCommune} from "../dataviz-commune/dataviz-commune"
import { Dataviz} from "../dataviz/dataviz"

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, About, DatavizCommune, Dataviz],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {
  protected readonly title = signal('chaire_pas');
}
