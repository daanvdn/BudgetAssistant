import { Injectable } from '@angular/core';
import { HttpRequest, HttpHandler, HttpEvent, HttpInterceptor } from '@angular/common/http';
import {firstValueFrom, from, Observable, switchMap} from 'rxjs';
import {JwtHelperService} from "@auth0/angular-jwt";
import {Configuration, TokenObtainPair, ApiBudgetAssistantBackendClientService, TokenRefresh} from "@daanvdn/budget-assistant-client";
import {AuthService} from "./auth/auth.service";

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  private readonly excludedUrls: string[] = [
    '/api/register/',
    '/api/token/'

  ];

  private jwtHelper = new JwtHelperService();

  constructor(
      private budgetAssistantBackendClientService: ApiBudgetAssistantBackendClientService,
      private config: Configuration,
      private authService: AuthService  // Inject AppService for credentials
  ) {}

  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    if (this.excludedUrls.some(url => req.url.includes(url))) {
      return next.handle(req); // Skip adding the Authorization header
    }
    return from(this.getValidToken()).pipe(
        switchMap(token => {
          if (token) {
            req = req.clone({
              setHeaders: { Authorization: `Bearer ${token}` }
            });
          }
          return next.handle(req);
        })
    );
  }

  private async getValidToken(): Promise<string | null> {
    let token = this.config.lookupCredential('jwtAuth') || sessionStorage.getItem('jwtToken');

    if (!token || this.jwtHelper.isTokenExpired(token)) {
      const refreshedToken = await this.refreshToken(token);
      return refreshedToken ? refreshedToken : this.retrieveNewToken();
    }
    return token;
  }

  private async refreshToken(token: string | null): Promise<string | null> {
    if (!token) return null;

    try {
      const refreshPayload: TokenRefresh = { refresh: token, access: '' };
      let source = this.budgetAssistantBackendClientService.apiTokenRefreshCreate(refreshPayload);
      const response: TokenRefresh = await firstValueFrom(source);

      this.config.credentials['jwtAuth'] = response.access;
      sessionStorage.setItem('jwtToken', response.access);  // Store in localStorage
      return response.access;
    } catch (error) {
      return null;
    }
  }

  private async retrieveNewToken(): Promise<string | null> {
    try {
      const user = await firstValueFrom(this.authService.getUserObservable());
      if (!user) return null;

      const loginPayload: TokenObtainPair = {
        username: user.userName as string,
        password: user.password as string,
        access: '',
        refresh: ''
      };

      const response: TokenObtainPair = await firstValueFrom(this.budgetAssistantBackendClientService.apiTokenCreate(loginPayload));

      this.config.credentials['jwtAuth'] = response.access;
      sessionStorage.setItem('jwtToken', response.access);  // Store in localStorage
      return response.access;
    } catch (error) {
      return null;
    }
  }
}