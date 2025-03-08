import {AfterViewInit, Component} from '@angular/core';
import { RouterOutlet } from '@angular/router';


@Component({
    selector: 'app-root',
    templateUrl: './app.component.html',
    styleUrls: ['./app.component.scss'],
    standalone: true,
    imports: [RouterOutlet],
})
export class AppComponent implements AfterViewInit {

  title:string = 'BudgetAssistant';






  constructor() {


  }





  public ngAfterViewInit(): void {






  }




}
