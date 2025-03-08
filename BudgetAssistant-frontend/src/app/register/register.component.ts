import {Component, OnInit} from '@angular/core';
import { AbstractControl, FormBuilder, FormGroup, ValidatorFn, Validators, FormsModule, ReactiveFormsModule } from "@angular/forms";
import {AuthService, RegisterFailureReason, RegisterResponse, Response} from "../auth/auth.service";
import {User} from "../model";
import {ErrorDialogService} from "../error-dialog/error-dialog.service";
import { MatCard, MatCardContent } from '@angular/material/card';
import { MatFormField, MatError, MatSuffix } from '@angular/material/form-field';
import { MatInput } from '@angular/material/input';
import { NgIf } from '@angular/common';
import { MatIconButton, MatButton } from '@angular/material/button';
import { MatIcon } from '@angular/material/icon';

@Component({
    selector: 'app-register',
    templateUrl: './register.component.html',
    styleUrls: ['./register.component.scss'],
    standalone: true,
    imports: [MatCard, MatCardContent, FormsModule, ReactiveFormsModule, MatFormField, MatInput, NgIf, MatError, MatIconButton, MatSuffix, MatIcon, MatButton]
})
export class RegisterComponent implements OnInit {

  form!: FormGroup;


  private formSubmitAttempt: boolean | undefined;

  hidePassword = true;

  togglePasswordVisibility(): void {
    this.hidePassword = !this.hidePassword;
  }

  constructor(private authService: AuthService, private fb: FormBuilder, private errorDialogService: ErrorDialogService) {

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


  ngOnInit(): void {

    this.form = this.fb.group({

      firstName: ['', [Validators.required, this.trimAndNotEmptyValidator()]],
      lastName: ['', [Validators.required, this.trimAndNotEmptyValidator()]],
      email: ['', [Validators.required, this.trimAndNotEmptyValidator()]],
      password: ['', [Validators.required, this.trimAndNotEmptyValidator()]]
    });
  }


  isFieldInvalid(field: string) {


    let fieldObj = this.form.get(field);
    if (fieldObj === undefined || fieldObj === null) {
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

  onSubmit() {
    if (!this.form) {
      throw new Error();
    }
    if (this.form.valid) {

      let user = this.form.value as User;

      this.authService.register(user).subscribe(response => {
        if (response.response == Response.FAILED) {

          this.errorDialogService.openErrorDialog("Registration failed!", this.getFailureErrorMessage(response))
           }
      });


    }
    this.formSubmitAttempt = true;
  }

  getFailureErrorMessage(response: RegisterResponse): string {
    if (response.failureReason == RegisterFailureReason.EMPTY_FIELDS) {
      return "Some fields are empty! All fields need to be filled out!"

    } else if (response.failureReason == RegisterFailureReason.USER_ALREADY_EXISTS) {
      return `User with email ${response.user.userName} already exists! Please choose another email!`
    } else if (response.failureReason == RegisterFailureReason.SERVER_ERROR) {
      return "There is a server error!"
    }

    throw new Error();

  }


}
