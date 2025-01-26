import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-boolean-radio-button-group',
  templateUrl: './boolean-radio-button-group.component.html',
  styleUrls: ['./boolean-radio-button-group.component.css']
})
export class BooleanRadioButtonGroupComponent implements OnInit {

  selectedValue!: Boolean
  constructor() { }

  ngOnInit() {
  }

}
