import {NgModule} from '@angular/core';
import {RouterModule, Routes} from '@angular/router';
import {InsightsComponent} from './insights/insights.component';
import {TransactionsComponent} from './transactions/transactions.component';
import {LoginComponent} from "./login/login.component";
import {AuthGuard} from "./auth/auth.guard";
import {HomeLayoutComponent} from "./layouts/home-layout/home-layout.component";
import {LoginLayoutComponent} from "./layouts/login-layout/login-layout.component";
import {ProfileComponent} from "./profile/profile.component";
import {RegisterComponent} from "./register/register.component";
import {BudgetComponent} from "./budget/budget.component";
import {RulesViewComponent} from "./rules-view/rules-view.component";
import {ManualCategorizationViewComponent} from "./manual-categorization-view/manual-categorization-view.component";

const routes: Routes =

  /*[
    {path: 'login', component: LoginComponent, outlet: "login_outlet"},
    {path: '', component: TransactionsComponent, canActivate: [AuthGuard]},
    {path: 'transacties', component: TransactionsComponent, canActivate: [AuthGuard]},
    {path: 'analyse', component: AnalysisComponent, canActivate: [AuthGuard]},
    {path: '**', component: LoginComponent, outlet: "login_outlet"},


  ];
*/
[
  {
    path: '',
    component: HomeLayoutComponent,
    canActivate: [AuthGuard],
    children: [
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
        component: RulesViewComponent
      },
      {
        path: 'categorieën',
        component: ManualCategorizationViewComponent
      }
    ]
  },
  {
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
  },
  {path: '**', redirectTo: ''}
];

@NgModule({
  imports: [RouterModule.forRoot(routes)
  ],
  exports: [RouterModule]
})
export class AppRoutingModule {
}
