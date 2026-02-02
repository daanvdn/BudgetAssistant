import {Injectable} from '@angular/core';
import {Router} from '@angular/router';
import {BehaviorSubject, map, Observable} from 'rxjs';

import {DUMMY_USER, User} from "../model";
import { HttpClient } from "@angular/common/http";
import {
  BudgetAssistantApiService, UserLogin, UserRegister,
} from '@daanvdn/budget-assistant-client';
import {ErrorDialogService} from "../error-dialog/error-dialog.service";
import {environment} from "../../environments/environment";

export enum Response {
  SUCCESS = "SUCCESS",
  FAILED = "FAILED",
}

export enum RegisterFailureReason{
  USER_ALREADY_EXISTS,
  EMPTY_FIELDS,
  SERVER_ERROR
}
export enum LoginFailureReason{
  PASSWORD_USER_COMBINATION_IS_WRONG,
  SERVER_ERROR
}

export interface LoginResponse {

  response: Response;
  errorMessage: string;
  user: User;
  failureReason: LoginFailureReason | null;


}
export interface RegisterResponse {

  response: Response;
  errorMessage: string;
  user: User;
  failureReason: RegisterFailureReason | null;


}

@Injectable({
  providedIn: 'root',
})

export class AuthService {
  private loggedIn: BehaviorSubject<boolean> = new BehaviorSubject<boolean>(false);
  private user: BehaviorSubject<User> = new BehaviorSubject<User>(DUMMY_USER);
  private devBypassChecked: boolean = false;


  constructor(private router: Router, private budgetAssistantApiService: BudgetAssistantApiService,
              private errorDialogService: ErrorDialogService,
              private http: HttpClient,
              ) {
    // DEV_AUTH_BYPASS: Auto-authenticate in dev mode by probing /api/auth/me
    this.probeDevBypass();
  }

  /**
   * DEV_AUTH_BYPASS: Probe the /api/auth/me endpoint on startup in dev mode.
   * If the backend has DEV_AUTH_BYPASS enabled and returns a user, auto-authenticate.
   */
  private probeDevBypass(): void {
    if (environment.production || !environment.devBypassHeader || this.devBypassChecked) {
      return;
    }
    this.devBypassChecked = true;

    // Create headers with the bypass header
    const headers: { [key: string]: string } = {};
    headers[environment.devBypassHeader] = '1';

    this.http.get<{ id: number; email: string; isActive: boolean }>(
      `${environment.API_BASE_PATH}/api/auth/me`,
      { headers }
    ).subscribe({
      next: (userResponse) => {
        console.log('DEV_AUTH_BYPASS: Auto-authenticated as', userResponse.email);
        // Create a dev user from the response
        const devUser: User = {
          ...DUMMY_USER,
          email: userResponse.email,
          userName: userResponse.email,
        };
        this.user.next(devUser);
        this.loggedIn.next(true);
      },
      error: (err) => {
        // Bypass not enabled on backend or failed - continue with normal auth flow
        console.log('DEV_AUTH_BYPASS: Probe failed, using normal auth flow', err.status);
      }
    });
  }


  get isLoggedIn() {
    return this.loggedIn.asObservable();
  }


  public getUserObservable(): Observable<User> {

    return this.user.asObservable();
  }


  public getUser(): User {
    return this.user.getValue();
  }


  login(user: User): Observable<LoginResponse> {
    const loginPayload: UserLogin = {
      email: user.email as string,
      password: user.password as string
    };
    return this.budgetAssistantApiService.authentication.loginApiAuthLoginPost(loginPayload, 'response').pipe(map(response => {
          if (!response.ok || !response.body?.accessToken) {
            this.loggedIn.next(false);
            return {
              response: Response.FAILED,
              errorMessage: response.statusText,
              user: DUMMY_USER,
              failureReason: LoginFailureReason.PASSWORD_USER_COMBINATION_IS_WRONG
            };

          }
          this.loggedIn.next(true);
          this.user.next(user);
          sessionStorage.setItem('jwtToken', response.body.accessToken);
          this.router.navigate(['/profiel']);
          return {
            response: Response.SUCCESS,
            errorMessage: '',
            user: user,
            failureReason: null
          }
        })
    );


  }

  register(user: User): Observable<RegisterResponse> {
    let registerUser:
        UserRegister = {
      email: user.email as string,
      password: user.password as string,

    }
    return this.budgetAssistantApiService.authentication.registerApiAuthRegisterPost(registerUser, 'response', true).pipe(map(response => {
      if (response.ok) {
        this.loggedIn.next(true);
        this.user.next(user);
        this.router.navigate(['/login']);
        return {
            response: Response.SUCCESS,
            errorMessage: '',
            user: user,
            failureReason: RegisterFailureReason.USER_ALREADY_EXISTS
        }
      }
      else {
        return {
          response: Response.FAILED,
          errorMessage: response.statusText,
          user: DUMMY_USER,
          failureReason: RegisterFailureReason.SERVER_ERROR
        }
      }
    }));




  }


  private parseRegisterResponse(data: any): RegisterResponse {
    return {
      ...data,
      failureReason: RegisterFailureReason[data.failureReason as keyof typeof RegisterFailureReason]
    };
  }


  logout() {
    this.loggedIn.next(false);
    this.user.next(DUMMY_USER);
    //Call this.logoutService.logoutCreate() and handle error response
    this.budgetAssistantApiService.authentication.logoutApiAuthLogoutPost('response').subscribe(response =>  {
      if (response.ok) {
        this.router.navigate(['/login']);

      }
      else {
        this.errorDialogService.openErrorDialog("Logout failed!", response.statusText);
      }
    });


  }
}