import {Injectable} from '@angular/core';
import {HttpClient} from "@angular/common/http";
import {AppService} from "./app.service";
import {Observable} from "rxjs";
import {RuleSetWrapper} from "./query-builder/query-builder.interfaces";
import {CategoryNode} from "./model";

@Injectable({
  providedIn: 'root'
})
export class CategoryRulesService {

  constructor(private http: HttpClient){
  }


  getExpenseRuleSetWrappers(): Observable<RuleSetWrapper> {
    return this.http.get<RuleSetWrapper>('/api/expense-rules');

  }
  getRevenueRuleSetWrappers(): Observable<RuleSetWrapper> {
    return this.http.get<RuleSetWrapper>('/api/revenue-rules');

  }

}
