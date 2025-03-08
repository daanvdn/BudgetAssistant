import { Component, OnInit } from '@angular/core';
import { MatRadioGroup, MatRadioButton } from '@angular/material/radio';
import { FormsModule } from '@angular/forms';

@Component({
    selector: 'app-boolean-radio-button-group',
    templateUrl: './boolean-radio-button-group.component.html',
    styleUrls: ['./boolean-radio-button-group.component.css'],
    standalone: true,
    imports: [MatRadioGroup, FormsModule, MatRadioButton]
})
export class BooleanRadioButtonGroupComponent implements OnInit {

  selectedValue!: Boolean
  constructor() { }

  ngOnInit() {
  }

}
