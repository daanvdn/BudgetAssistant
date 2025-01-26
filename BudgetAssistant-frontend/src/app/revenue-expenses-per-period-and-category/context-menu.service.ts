import { Injectable } from '@angular/core';

export interface CategoryAndPeriod{
    category: string;
    period: string;

}
@Injectable({
  providedIn: 'root'
})
export class ContextMenuService {
  data: any;

  setData(data: CategoryAndPeriod): void {
    this.data = data;
  }

  getData() : CategoryAndPeriod{
    return this.data;
  }
}