
import {Injectable} from '@angular/core';
import {ActivatedRouteSnapshot, CanActivate, Router, RouterStateSnapshot} from '@angular/router';
import {Observable, of} from 'rxjs';
import {AuthService} from "./auth.service";
import {map, take} from 'rxjs/operators';
import {environment} from "../../environments/environment";

@Injectable()
export class AuthGuard implements CanActivate    {
  constructor(private authService: AuthService, private router: Router) {
  }

  canActivate(next: ActivatedRouteSnapshot, state: RouterStateSnapshot): Observable<boolean> {
    // DEV_AUTH_BYPASS: Allow navigation in dev mode when bypass is enabled
    if (!environment.production && environment.devBypassHeader) {
      return of(true);
    }

    return this.authService.isLoggedIn.pipe(
      take(1),
      map((isLoggedIn: boolean) => {
        if (!isLoggedIn) {
          this.router.navigate(['/login']);
          return false;
        }
        return true;
      })
    );
  }
}
