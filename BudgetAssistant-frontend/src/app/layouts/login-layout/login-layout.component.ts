import { Component, OnInit } from '@angular/core';
import { RouterOutlet } from '@angular/router';

@Component({
    selector: 'app-login-layout',
    templateUrl: './login-layout.component.html',
    styleUrls: ['./login-layout.component.css'],
    standalone: true,
    imports: [RouterOutlet]
})
export class LoginLayoutComponent implements OnInit {

  constructor() { }

  ngOnInit(): void {
  }

}
