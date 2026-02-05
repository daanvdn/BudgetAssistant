import { Component, OnInit } from '@angular/core';
import { NavigationComponent } from '../../navigation/navigation.component';
import { RouterOutlet } from '@angular/router';

@Component({
    selector: 'app-home-layout',
    templateUrl: './home-layout.component.html',
    styleUrls: ['./home-layout.component.css'],
    standalone: true,
    imports: [NavigationComponent, RouterOutlet]
})
export class HomeLayoutComponent implements OnInit {

  constructor() { }

  ngOnInit(): void {
  }

}
