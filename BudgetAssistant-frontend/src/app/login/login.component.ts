import {Component, OnInit} from '@angular/core';
import { AbstractControl, FormBuilder, FormGroup, ValidatorFn, Validators, FormsModule, ReactiveFormsModule } from '@angular/forms';

import {AuthService, Response} from '../auth/auth.service';
import {User} from "../model";
import {ErrorDialogService} from "../error-dialog/error-dialog.service";
import { MatCard, MatCardContent } from '@angular/material/card';
import { MatFormField, MatError, MatSuffix } from '@angular/material/form-field';
import { MatInput } from '@angular/material/input';
import { NgIf } from '@angular/common';
import { MatIconButton, MatButton } from '@angular/material/button';
import { MatIcon } from '@angular/material/icon';
import { RouterLink, RouterLinkActive } from '@angular/router';

@Component({
    selector: 'app-login',
    templateUrl: './login.component.html',
    styleUrls: ['./login.component.scss'],
    standalone: true,
    imports: [MatCard, MatCardContent, FormsModule, ReactiveFormsModule, MatFormField, MatInput, NgIf, MatError, MatIconButton, MatSuffix, MatIcon, MatButton, RouterLink, RouterLinkActive]
})
export class LoginComponent implements OnInit {

  form: FormGroup;
  private formSubmitAttempt: boolean | undefined;
  hidePassword = true;

  constructor(
    private fb: FormBuilder,
    private authService: AuthService, private errorDialogService: ErrorDialogService
  ) {
    this.form = this.fb.group({
      userName: ['', [Validators.required, this.trimAndNotEmptyValidator()]],
      password: ['', [Validators.required, this.trimAndNotEmptyValidator()]]
    });
  }

  ngOnInit() {



  }




  private trimAndNotEmptyValidator(): ValidatorFn {
    return (control: AbstractControl): { [key: string]: any } | null => {
      if (control.value) {
        // Trim the input and check if it's empty after trimming.
        const trimmedValue = control.value.trim();
        if (trimmedValue === '') {
          return {empty: true}; // Return a validation error if empty.
        }
      }
      return null; // Return null if the input is valid.
    };
  }

  isFieldInvalid(field: string) {


    let fieldObj = this.form.get(field);
    if(fieldObj === undefined || fieldObj === null){
      return false;
    }
    let valid = fieldObj.valid;
    // @ts-ignore
    let touched = fieldObj.touched;
    // @ts-ignore
    let untouched = fieldObj.untouched;
    return (
      (!valid && touched) ||
      (untouched && this.formSubmitAttempt)
    );
  }

  doLogin() {
    if(!this.form){
      throw new Error();
    }
    if (this.form.valid) {

      let user = this.form.value as User;
      if (user.userName == '' || user.password == '') {
        this.errorDialogService.openErrorDialog("Gebruikersnaam en paswoord moeten beiden ingevuld zijn!", undefined)
      } else {
        this.authService.login(this.form.value).subscribe(response => {
          if(response.response == Response.FAILED){
            this.errorDialogService.openErrorDialog("Aanmelden is mislukt!", response.errorMessage)
          }
        });

      }
    }
    this.formSubmitAttempt = true;
  }
}
