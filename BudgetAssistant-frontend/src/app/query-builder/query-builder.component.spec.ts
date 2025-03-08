import { ComponentFixture, TestBed } from '@angular/core/testing';
import {deserializeRuleSet, RuleSet, Rule, FIELDS_BY_NAME_MAP} from './query-builder.interfaces';
import { QueryBuilderComponent } from './query-builder.component';

describe('QueryBuilderComponent', () => {
  let component: QueryBuilderComponent;
  let fixture: ComponentFixture<QueryBuilderComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
    imports: [QueryBuilderComponent]
})
    .compileComponents();

    fixture = TestBed.createComponent(QueryBuilderComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});


//test deserialization of RuleSet object
//{"clazz":"RuleSet","condition":"AND","rules":[{"clazz":"Rule","field":["Counterparty Name"],"fieldType":"string","fieldMatchType":"any of","operator":{"name":"contains","value":"contains","type":"string"},"value":["sdsds","sdsd"],"valueMatchType":"any of"}]}



describe('deserializeRuleSet_1', () => {
  it('should correctly deserialize a RuleSet from a JSON string', () => {
    const jsonString = '{"clazz":"RuleSet","condition":"AND","rules":[{"clazz":"Rule","field":["Counterparty Name"],"fieldType":"string","fieldMatchType":"any of","operator":{"name":"contains","value":"contains","type":"string"},"value":["sdsds","sdsd"],"valueMatchType":"any of"}]}';
    const result = deserializeRuleSet(jsonString);

    expect(result).toBeInstanceOf(RuleSet);
    expect(result.condition).toEqual('AND');
    expect(result.rules.length).toEqual(1);
    expect(result.rules[0]).toBeInstanceOf(Rule);
    expect(result.rules[0].field).toEqual([FIELDS_BY_NAME_MAP.get('Counterparty Name')]);
    expect(result.rules[0].fieldType).toEqual('string');
    expect(result.rules[0].fieldMatchType).toEqual('any of');
    expect(result.rules[0].operator.name).toEqual('contains');
    expect(result.rules[0].operator.value).toEqual('contains');
    expect(result.rules[0].operator.type).toEqual('string');
    expect(result.rules[0].value).toEqual(['sdsds', 'sdsd']);
    expect(result.rules[0].valueMatchType).toEqual('any of');
  });

  it('should throw an error when the JSON string is not a valid RuleSet', () => {
    const jsonString = '{"invalid":"json"}';
    expect(() => deserializeRuleSet(jsonString)).toThrow();
  });
});
describe('deserializeRuleSet_2', () => {
  it('should correctly deserialize a RuleSet from a JSON string', () => {
    const jsonString = '{"clazz": "RuleSet", "condition": "AND", "rules": [{"clazz": "Rule", "field": ["Counterparty Name"], "fieldMatchType": "any of", "fieldType": "string", "operator": {"name": "contains", "type": "string", "value": "contains"}, "value": ["sdsds", "sdsd"], "valueMatchType": "any of"}, {"clazz": "Rule", "field": ["Counterparty Name"], "fieldMatchType": "any of", "fieldType": "string", "operator": {"name": "contains", "type": "string", "value": "contains"}, "value": ["sdsds", "sdsd"], "valueMatchType": "any of"}]}';
    const result = deserializeRuleSet(jsonString);

    expect(result).toBeInstanceOf(RuleSet);
    expect(result.condition).toEqual('AND');
    expect(result.rules.length).toEqual(2);
    expect(result.rules[0]).toBeInstanceOf(Rule);
    expect(result.rules[0].field).toEqual([FIELDS_BY_NAME_MAP.get('Counterparty Name')]);
    expect(result.rules[0].fieldType).toEqual('string');
    expect(result.rules[0].fieldMatchType).toEqual('any of');
    expect(result.rules[0].operator.name).toEqual('contains');
    expect(result.rules[0].operator.value).toEqual('contains');
    expect(result.rules[0].operator.type).toEqual('string');
    expect(result.rules[0].value).toEqual(['sdsds', 'sdsd']);
    expect(result.rules[0].valueMatchType).toEqual('any of');
    expect(result.rules[1]).toBeInstanceOf(Rule);
    expect(result.rules[1].field).toEqual([FIELDS_BY_NAME_MAP.get('Counterparty Name')]);
    expect(result.rules[1].fieldType).toEqual('string');
    expect(result.rules[1].fieldMatchType).toEqual('any of');
    expect(result.rules[1].operator.name).toEqual('contains');
    expect(result.rules[1].operator.value).toEqual('contains');
    expect(result.rules[1].operator.type).toEqual('string');
    expect(result.rules[1].value).toEqual(['sdsds', 'sdsd']);
    expect(result.rules[1].valueMatchType).toEqual('any of');
  });

  it('should throw an error when the JSON string is not a valid RuleSet', () => {
    const jsonString = '{"invalid":"json"}';
    expect(() => deserializeRuleSet(jsonString)).toThrow();
  });
});
describe('deserializeRuleSet_3', () => {
  it('should correctly deserialize a RuleSet from a JSON string', () => {
    const jsonString = '{"clazz": "RuleSet", "condition": "AND", "rules": [{"clazz": "Rule", "field": ["Counterparty Name"], "fieldMatchType": "any of", "fieldType": "string", "operator": {"name": "contains", "type": "string", "value": "contains"}, "value": ["sdsds", "sdsd"], "valueMatchType": "any of"}, {"clazz": "Rule", "field": ["Counterparty Name"], "fieldMatchType": "any of", "fieldType": "string", "operator": {"name": "contains", "type": "string", "value": "contains"}, "value": ["sdsds", "sdsd"], "valueMatchType": "any of"}, {"clazz": "RuleSet", "condition": "AND", "rules": [{"clazz": "Rule", "field": ["Counterparty Name"], "fieldMatchType": "any of", "fieldType": "string", "operator": {"name": "contains", "type": "string", "value": "contains"}, "value": ["sdsds", "sdsd"], "valueMatchType": "any of"}, {"clazz": "Rule", "field": ["Counterparty Name"], "fieldMatchType": "any of", "fieldType": "string", "operator": {"name": "contains", "type": "string", "value": "contains"}, "value": ["sdsds", "sdsd"], "valueMatchType": "any of"}]}]}';
    const result = deserializeRuleSet(jsonString);

    expect(result).toBeInstanceOf(RuleSet);
    expect(result.condition).toEqual('AND');
    expect(result.rules.length).toEqual(3);
    let firstElement = result.rules[0];
    expect(firstElement).toBeInstanceOf(Rule);
    expect(firstElement.field).toEqual([FIELDS_BY_NAME_MAP.get('Counterparty Name')]);
    expect(firstElement.fieldType).toEqual('string');
    expect(firstElement.fieldMatchType).toEqual('any of');
    expect(firstElement.operator.name).toEqual('contains');
    expect(firstElement.operator.value).toEqual('contains');
    expect(firstElement.operator.type).toEqual('string');
    expect(firstElement.value).toEqual(['sdsds', 'sdsd']);
    expect(firstElement.valueMatchType).toEqual('any of');
    let secondElement = result.rules[1];
    expect(secondElement).toBeInstanceOf(Rule);
    expect(secondElement.field).toEqual([FIELDS_BY_NAME_MAP.get('Counterparty Name')]);
    expect(secondElement.fieldType).toEqual('string');
    expect(secondElement.fieldMatchType).toEqual('any of');
    expect(secondElement.operator.name).toEqual('contains');
    expect(secondElement.operator.value).toEqual('contains');
    expect(secondElement.operator.type).toEqual('string');
    expect(secondElement.value).toEqual(['sdsds', 'sdsd']);
    expect(secondElement.valueMatchType).toEqual('any of');

    let thirdElement = result.rules[2];
    expect(thirdElement).toBeInstanceOf(RuleSet);
    expect(thirdElement.condition).toEqual('AND');
    expect(thirdElement.rules.length).toEqual(2);


    let firstElementOfNestedRuleSet = thirdElement.rules[0];
    expect(firstElementOfNestedRuleSet).toBeInstanceOf(Rule);
    expect(firstElementOfNestedRuleSet.field).toEqual([FIELDS_BY_NAME_MAP.get('Counterparty Name')]);
    expect(firstElementOfNestedRuleSet.fieldType).toEqual('string');
    expect(firstElementOfNestedRuleSet.fieldMatchType).toEqual('any of');
    expect(firstElementOfNestedRuleSet.operator.name).toEqual('contains');
    expect(firstElementOfNestedRuleSet.operator.value).toEqual('contains');
    expect(firstElementOfNestedRuleSet.operator.type).toEqual('string');
    expect(firstElementOfNestedRuleSet.value).toEqual(['sdsds', 'sdsd']);
    expect(firstElementOfNestedRuleSet.valueMatchType).toEqual('any of');
    let secondElementOfNestedRuleSet = thirdElement.rules[1];
    expect(secondElementOfNestedRuleSet).toBeInstanceOf(Rule);
    expect(secondElementOfNestedRuleSet.field).toEqual([FIELDS_BY_NAME_MAP.get('Counterparty Name')]);
    expect(secondElementOfNestedRuleSet.fieldType).toEqual('string');
    expect(secondElementOfNestedRuleSet.fieldMatchType).toEqual('any of');
    expect(secondElementOfNestedRuleSet.operator.name).toEqual('contains');
    expect(secondElementOfNestedRuleSet.operator.value).toEqual('contains');
    expect(secondElementOfNestedRuleSet.operator.type).toEqual('string');
    expect(secondElementOfNestedRuleSet.value).toEqual(['sdsds', 'sdsd']);
    expect(secondElementOfNestedRuleSet.valueMatchType).toEqual('any of');




  });

  it('should throw an error when the JSON string is not a valid RuleSet', () => {
    const jsonString = '{"invalid":"json"}';
    expect(() => deserializeRuleSet(jsonString)).toThrow();
  });
});

