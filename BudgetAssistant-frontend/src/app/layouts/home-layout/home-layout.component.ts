import { Component, OnInit } from '@angular/core';
import { NavigationComponent } from '../../navigation/navigation.component';

@Component({
    selector: 'app-home-layout',
    templateUrl: './home-layout.component.html',
    styleUrls: ['./home-layout.component.css'],
    standalone: true,
    imports: [NavigationComponent]
})
export class HomeLayoutComponent implements OnInit {

  constructor() { }

  ngOnInit(): void {
  }

}
