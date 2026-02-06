import {NgModule} from '@angular/core';
import {RouterModule, Routes, Route} from '@angular/router';
import {InsightsComponent} from './insights/insights.component';
import {LoginComponent} from "./login/login.component";
import {AuthGuard} from "./auth/auth.guard";
import {HomeLayoutComponent} from "./layouts/home-layout/home-layout.component";
import {LoginLayoutComponent} from "./layouts/login-layout/login-layout.component";
import {ProfileComponent} from "./profile/profile.component";
import {RegisterComponent} from "./register/register.component";
import {BudgetComponent} from "./budget/budget.component";
import {RulesPageComponent} from "./rules/rules-page.component";
import {ManualCategorizationViewComponent} from "./manual-categorization-view/manual-categorization-view.component";
import {environment} from '../environments/environment';
import {TransactionsComponent} from "./transactions/transactions.component";

const childRoutes: Routes = [
    {
        path: '',
        redirectTo: 'transacties',
        pathMatch: 'full'
    },
    {
        path: 'profiel',
        component: ProfileComponent
    },
    {
        path: 'transacties',
        component: TransactionsComponent
    },
    {
        path: 'inzichten',
        component: InsightsComponent
    },
    {
        path: 'budget',
        component: BudgetComponent
    },
    {
        path: 'regels',
        component: RulesPageComponent
    },
    {
        path: 'categorieën',
        component: ManualCategorizationViewComponent
    }
];

const homeRoute: Route = environment.production
    ? {
        path: '',
        component: HomeLayoutComponent,
        canActivate: [AuthGuard],
        children: childRoutes
    }
    : {
        path: '',
        component: HomeLayoutComponent,
        children: childRoutes
    };

const loginRoutes: Routes = environment.production
    ? [{
        path: '',
        component: LoginLayoutComponent,
        children: [
            {
                path: 'login',
                component: LoginComponent
            },
            {
                path: 'register',
                component: RegisterComponent
            }
        ]
    }]
    : [];

const routes: Routes = [
    homeRoute,
    ...loginRoutes,
    {path: '**', redirectTo: ''}
];

@NgModule({
    imports: [RouterModule.forRoot(routes, { enableTracing: false})],
    exports: [RouterModule]
})
export class AppRoutingModule {
}
