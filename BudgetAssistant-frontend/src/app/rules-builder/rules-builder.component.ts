import {Component, Input, OnChanges, OnInit, SimpleChanges} from '@angular/core';
import {
  DEFAULT_QUERY_BUILDER_CONFIG, QueryBuilderConfig, RuleSet, RuleSetWrapper
} from "../query-builder/query-builder.interfaces";
import {AppService} from "../app.service";
import {AuthService} from "../auth/auth.service";
import {ErrorDialogService} from "../error-dialog/error-dialog.service";
import {CategoryNode, CategoryType} from "../model";
import { QueryBuilderComponent } from '../query-builder/query-builder.component';
import { FormsModule } from '@angular/forms';


@Component({
    selector: 'category-rules',
    templateUrl: './rules-builder.component.html',
    styleUrls: ['./rules-builder.component.scss'],
    standalone: true,
    imports: [QueryBuilderComponent, FormsModule]
})
export class RulesBuilderComponent implements OnInit, OnChanges {

  @Input() categoryNode!: CategoryNode;

  ruleSet!: RuleSet;

  ruleSetWrapper!: RuleSetWrapper;


  config: QueryBuilderConfig = DEFAULT_QUERY_BUILDER_CONFIG;

  constructor(private appService: AppService, private authService: AuthService,
              private errorDialogService: ErrorDialogService) {


  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['categoryNode']) {
      // categoryNode input has changed, do something with it
      let categoryType: CategoryType = this.categoryNode.type as CategoryType;
      let user = this.authService.getUser();
      if (!user || !user.userName) {
        this.errorDialogService.openErrorDialog("User is not defined!", undefined);
        return;
      }
      this.appService.getOrCreateRuleSetWrapper(this.categoryNode, categoryType, user.userName)
            .subscribe((response: RuleSetWrapper) => {
              this.ruleSetWrapper = response;
              this.ruleSet = this.ruleSetWrapper.ruleSet;
            });


    }


  }

  ngOnInit(): void {
  }


  onRuleSetWrapperChange() {
    if (this.ruleSet.isComplete()) {

      this.appService.saveRuleSetWrapper(this.ruleSetWrapper).subscribe((response: any) => {
      });


    }
  }
}
