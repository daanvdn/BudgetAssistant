import {Injectable} from '@angular/core';
import {Router} from '@angular/router';
import {BehaviorSubject, map, Observable} from 'rxjs';

import {DUMMY_USER, User} from "../model";
import {HttpClient} from "@angular/common/http";
import {
  ApiBudgetAssistantBackendClientService,
  RegisterUser,
  TokenObtainPair,
} from '@daanvdn/budget-assistant-client';
import {ErrorDialogService} from "../error-dialog/error-dialog.service";

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


  constructor(private router: Router, private apiBudgetAssistantBackendClientService: ApiBudgetAssistantBackendClientService,
              private errorDialogService: ErrorDialogService,
              ) {

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
    const loginPayload: TokenObtainPair = {
      username: user.userName as string,
      password: user.password as string,
      access: '',
      refresh: ''
    };
    return this.apiBudgetAssistantBackendClientService.apiTokenCreate(loginPayload, 'response').pipe(map(response => {
          if (!response.ok || !response.body?.access) {
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
          sessionStorage.setItem('jwtToken', response.body.access);
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
    let registerUser
        :
        RegisterUser = {
      username: user.email as string,
      password: user.password as string,
      email: user.email as string,

    }
    return this.apiBudgetAssistantBackendClientService.apiRegisterCreate(registerUser, 'response', true).pipe(map(response => {
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
    this.apiBudgetAssistantBackendClientService.apiLogoutCreate('response').subscribe(response => {
      if (response.ok) {
        this.router.navigate(['/login']);

      }
      else {
        this.errorDialogService.openErrorDialog("Logout failed!", response.statusText);
      }
    });


  }
}