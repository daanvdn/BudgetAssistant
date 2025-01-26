import {Injectable} from '@angular/core';
import {Router} from '@angular/router';
import {BehaviorSubject, map, Observable} from 'rxjs';

import {DUMMY_USER, User} from "../model";
import {HttpClient} from "@angular/common/http";
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
  failureReason: LoginFailureReason;


}
export interface RegisterResponse {

  response: Response;
  errorMessage: string;
  user: User;
  failureReason: RegisterFailureReason;


}

@Injectable()
export class AuthService {
  private loggedIn: BehaviorSubject<boolean> = new BehaviorSubject<boolean>(false);
  private user: BehaviorSubject<User> = new BehaviorSubject<User>(DUMMY_USER);

  constructor(private router: Router, private http: HttpClient){

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


    const params = {
      user: JSON.stringify(user),
      responseType: "json"

    }
    return this.http.get<LoginResponse>("http://localhost:8080/loginUser", {params}).pipe(map(response => {
        if (response.response == Response.SUCCESS) {
          let userFromResponse = response.user
          this.loggedIn.next(true);
          this.user.next(userFromResponse);
          this.router.navigate(['/profiel']);
        } else {
          this.loggedIn.next(false);
        }
        return response
      }
    ))


  }

  register(user: User): Observable<RegisterResponse> {


    const params = {
      user: JSON.stringify(user),
      responseType: "json"

    }
    return this.http.get<RegisterResponse>("http://localhost:8080/registerUser", {params}).pipe(
      map(response => this.parseRegisterResponse(response))
    ).pipe(map(response => {
        if (response.response == Response.SUCCESS) {

          this.loggedIn.next(true);
          this.user.next(user);
          this.router.navigate(['/login']);
        } else {
          this.loggedIn.next(false);
        }
        return response
      }
    ))


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
    this.router.navigate(['/login']);
  }


}
