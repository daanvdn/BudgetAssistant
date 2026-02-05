import { Injectable } from '@angular/core';
import { HttpRequest, HttpHandler, HttpEvent, HttpInterceptor } from '@angular/common/http';
import { Observable } from 'rxjs';
import { JwtHelperService } from "@auth0/angular-jwt";
import { Configuration } from "@daanvdn/budget-assistant-client";
import { Router } from '@angular/router';
import { environment } from "../environments/environment";

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  private readonly excludedUrls: string[] = [
    '/api/auth/register',
    '/api/auth/login',
    '/api/auth/forgot-password',
    '/api/auth/reset-password'
  ];

  private jwtHelper = new JwtHelperService();

  constructor(
      private config: Configuration,
      private router: Router
  ) {}

  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    // DEV_AUTH_BYPASS: Add bypass header in development mode and skip token validation
    if (!environment.production && environment.devBypassHeader) {
      req = req.clone({
        setHeaders: { [environment.devBypassHeader]: '1' }
      });
      // In dev mode with bypass enabled, skip token validation - backend handles auth via bypass header
      return next.handle(req);
    }

    // Skip auth header for excluded URLs (public endpoints)
    if (this.excludedUrls.some(url => req.url.includes(url))) {
      return next.handle(req);
    }

    // Get token from config or sessionStorage
    const token = this.config.lookupCredential('jwtAuth') || sessionStorage.getItem('jwtToken');

    // If no token or token is expired, clear storage and redirect to login
    if (!token || this.jwtHelper.isTokenExpired(token)) {
      this.clearTokenAndRedirectToLogin();
      return next.handle(req);
    }

    // Add Authorization header with valid token
    const authReq = req.clone({
      setHeaders: { Authorization: `Bearer ${token}` }
    });

    return next.handle(authReq);
  }

  /**
   * Clear the expired/invalid token and redirect user to login page.
   * The FastAPI backend does not support token refresh, so users must re-authenticate.
   */
  private clearTokenAndRedirectToLogin(): void {
    sessionStorage.removeItem('jwtToken');
    if (this.config.credentials) {
      delete this.config.credentials['jwtAuth'];
    }
    // Only redirect if not already on a public page
    const currentUrl = this.router.url;
    if (!currentUrl.includes('/login') && !currentUrl.includes('/register')) {
      this.router.navigate(['/login']);
    }
  }
}