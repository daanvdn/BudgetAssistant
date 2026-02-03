import {enableProdMode, importProvidersFrom} from '@angular/core';


import {environment} from './environments/environment';
import {
    BudgetAssistantApiService,
    ApiModule,
    BASE_PATH,
    Configuration
} from '@daanvdn/budget-assistant-client';
import {AuthService} from './app/auth/auth.service';
import {AuthGuard} from './app/auth/auth.guard';
import {DatePipe} from '@angular/common';
import {HTTP_INTERCEPTORS, provideHttpClient, withInterceptorsFromDi} from '@angular/common/http';
import {AuthInterceptor} from './app/auth.interceptor';
import {CdkMenuModule} from '@angular/cdk/menu';
import {NgSelectModule} from '@ng-select/ng-select';
import {provideAnimations} from '@angular/platform-browser/animations';
import {MatTooltipModule} from '@angular/material/tooltip';
import {MatSortModule} from '@angular/material/sort';
import {MatTreeModule} from '@angular/material/tree';
import {MatAutocompleteModule} from '@angular/material/autocomplete';
import {MatFormFieldModule} from '@angular/material/form-field';
import {NgxChartsModule} from '@swimlane/ngx-charts';
import {bootstrapApplication, BrowserModule} from '@angular/platform-browser';
import {AppRoutingModule} from './app/app-routing.module';
import {FormsModule, ReactiveFormsModule} from '@angular/forms';
import {MatNativeDateModule} from '@angular/material/core';
import {MatToolbarModule} from '@angular/material/toolbar';
import {MatButtonModule} from '@angular/material/button';
import {MatDialogModule} from '@angular/material/dialog';
import {MatInputModule} from '@angular/material/input';
import {MatSelectModule} from '@angular/material/select';
import {MatTableModule} from '@angular/material/table';
import {MatPaginatorModule} from '@angular/material/paginator';
import {MatDatepickerModule} from '@angular/material/datepicker';
import {MatCardModule} from '@angular/material/card';
import {MatCheckboxModule} from '@angular/material/checkbox';
import {MatRadioModule} from '@angular/material/radio';
import {MatSidenavModule} from '@angular/material/sidenav';
import {MatListModule} from '@angular/material/list';
import {MatIconModule} from '@angular/material/icon';
import {MatGridListModule} from '@angular/material/grid-list';
import {MatProgressSpinnerModule} from '@angular/material/progress-spinner';
import {FontAwesomeModule} from '@fortawesome/angular-fontawesome';
import {MatTabsModule} from '@angular/material/tabs';
import {MatButtonToggleModule} from '@angular/material/button-toggle';
import {MatExpansionModule} from '@angular/material/expansion';
import {MatBadgeModule} from '@angular/material/badge';
import {ChartModule} from 'primeng/chart';
import {TreeTableModule} from 'primeng/treetable';
import {AppComponent} from './app/app.component';
import {
    provideTanStackQuery,
    QueryClient,
} from '@tanstack/angular-query-experimental'

if (environment.production) {
  enableProdMode();
}

bootstrapApplication(AppComponent, {
    providers: [
        importProvidersFrom(CdkMenuModule, NgSelectModule, MatTooltipModule, MatSortModule, MatTreeModule,
            MatAutocompleteModule, MatFormFieldModule, NgxChartsModule, BrowserModule, AppRoutingModule,
            FormsModule, MatNativeDateModule, ReactiveFormsModule, MatToolbarModule, MatButtonModule, MatDialogModule,
            MatInputModule, MatSelectModule, MatTableModule, MatSortModule, MatPaginatorModule, MatNativeDateModule,
            MatDatepickerModule, MatCardModule, MatCheckboxModule, MatRadioModule, MatSidenavModule, MatListModule,
            MatIconModule, MatGridListModule, MatProgressSpinnerModule,
            FontAwesomeModule, MatTabsModule, MatButtonToggleModule, MatExpansionModule,
            MatBadgeModule, ChartModule, TreeTableModule,
            ApiModule.forRoot(() => {
            return new Configuration({
                basePath: environment.API_BASE_PATH,
            });
        })),
        BudgetAssistantApiService,
        AuthService, AuthGuard,
        DatePipe,
        { provide: HTTP_INTERCEPTORS, useClass: AuthInterceptor, multi: true },
        {
            provide: Configuration,
            useFactory: () => new Configuration(),
        },
        { provide: BASE_PATH, useValue: environment.API_BASE_PATH },
        provideHttpClient(withInterceptorsFromDi()),
        provideAnimations(),
        provideTanStackQuery(new QueryClient())
    ]
})
  .catch(err => console.error(err));
