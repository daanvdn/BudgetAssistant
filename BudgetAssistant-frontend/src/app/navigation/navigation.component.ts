import {Component, inject} from '@angular/core';
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
import {RoutePrefetchService} from '../shared/route-prefetch.service';

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
    private readonly prefetch = inject(RoutePrefetchService);

    constructor(private authService: AuthService) {}

    onLogout(): void {
        this.authService.logout();
    }

    onPrefetch(route: string): void {
        switch (route) {
            case '/transacties':  this.prefetch.prefetchTransactions(); break;
            case '/budget':       this.prefetch.prefetchBudget(); break;
            case '/regels':       this.prefetch.prefetchRules(); break;
        }
    }

    // Font Awesome icons
    protected readonly faUser = faUser;
    protected readonly faDollarSign = faDollarSign;
    protected readonly faChartPie = faChartPie;
    protected readonly faNetworkWired = faNetworkWired;
    protected readonly faScaleBalanced = faScaleBalanced;
    protected readonly faRightFromBracket = faRightFromBracket;
}
