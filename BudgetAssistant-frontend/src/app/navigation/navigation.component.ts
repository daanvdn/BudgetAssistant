import {Component} from '@angular/core';
import {AuthService} from "../auth/auth.service";
import {
    faChartPie,
    faDollarSign,
    faNetworkWired,
    faRightFromBracket,
    faScaleBalanced,
    faUser
} from "@fortawesome/free-solid-svg-icons";
import {MatDrawer, MatDrawerContainer, MatDrawerContent} from '@angular/material/sidenav';
import {MatListItem, MatNavList} from '@angular/material/list';
import {MatDivider} from '@angular/material/divider';
import {RouterLink, RouterLinkActive} from '@angular/router';
import {FaIconComponent} from '@fortawesome/angular-fontawesome';

@Component({
    selector: 'app-navigation',
    templateUrl: './navigation.component.html',
    styleUrls: ['./navigation.component.scss'],
    standalone: true,
    imports: [
        MatDrawerContainer,
        MatDrawer,
        MatNavList,
        MatListItem,
        MatDivider,
        MatDrawerContent,
        RouterLink,
        RouterLinkActive,
        FaIconComponent
    ]
})
export class NavigationComponent {

    constructor(private authService: AuthService) {}

    onLogout(): void {
        this.authService.logout();
    }

    // Font Awesome icons
    protected readonly faUser = faUser;
    protected readonly faDollarSign = faDollarSign;
    protected readonly faChartPie = faChartPie;
    protected readonly faNetworkWired = faNetworkWired;
    protected readonly faScaleBalanced = faScaleBalanced;
    protected readonly faRightFromBracket = faRightFromBracket;
}
