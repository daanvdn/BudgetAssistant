import { Component, OnInit } from '@angular/core';
import {AuthService} from "../auth/auth.service";
import {Observable} from "rxjs";
import {
  faChartPie,
  faDollarSign,
  faNetworkWired,
  faRightFromBracket,
  faScaleBalanced,
  faUser,
  faTag
} from "@fortawesome/free-solid-svg-icons";

@Component({
  selector: 'app-navigation',
  templateUrl: './navigation.component.html',
  styleUrls: ['./navigation.component.scss']
})
export class NavigationComponent implements OnInit {



  // isLoggedIn$: Observable<boolean>;

  constructor(public authService: AuthService) {
    // this.isLoggedIn$ = this.authService.isLoggedIn;
  }

  ngOnInit() {
    // this.isLoggedIn$ = this.authService.isLoggedIn;
  }

  onLogout() {
    this.authService.logout();
  }


  protected readonly faNetworkWired = faNetworkWired;
  protected readonly faUser = faUser;
  protected readonly faDollarSign = faDollarSign;
  protected readonly faChartPie = faChartPie;
  protected readonly faScaleBalanced = faScaleBalanced;
  protected readonly faRightFromBracket = faRightFromBracket;
  protected readonly faTag = faTag;
}
