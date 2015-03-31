/**
 * Field model
 */
function Field(data){
  'use strict';

  var self = this;

  self.__url__ = ko.observable();
  self.id = ko.observable();
  self.name = ko.observable();
  self.title = ko.observable();
  self.description = ko.observable();
  self.type = ko.observable();
  self.is_required = ko.observable();
  self.is_collection = ko.observable();
  self.is_private = ko.observable();
  self.is_shuffled = ko.observable();
  self.is_readonly = ko.observable();
  self.is_system = ko.observable();
  self.pattern = ko.observable();
  self.decimal_places = ko.observable();
  self.value_min = ko.observable();
  self.value_max = ko.observable();
  self.fields = ko.observableArray();
  self.choices = ko.observableArray();

  self.isNew = ko.pureComputed(function(){ return !self.id(); });

  self.hasFields = ko.pureComputed(function(){
    return self.fields().length > 0;
  });

  self.isType = function(){
    return Array.prototype.slice.call(arguments).some(function(value){
      return value == self.type();
    });
  };

  self.isLimitAllowed = ko.pureComputed(function(){
    return self.isType('string', 'number')
      || (self.isType('choice') && self.is_collection());
  });

  self.choiceInputType = ko.pureComputed(function(){
    return self.is_collection() ? 'checkbox' : 'radio';
  });

  self.isSection = ko.pureComputed(function(){
    return self.type() == 'section';
  });

  self.doAddChoice = function(){
    self.choices.push(new Choice({}));
  };

  self.doDeleteChoice = function(data, event){
      self.choices.remove(data);
  };

  self.update = function(data) {
    data = data || {};
    self.__url__(data.__url__);
    self.id(data.id);
    self.name(data.name);
    self.title(data.title);
    self.description(data.description);
    self.type(data.type);
    self.is_required(data.is_required);
    self.is_collection(data.is_collection);
    self.is_private(data.is_private);
    self.is_shuffled(data.is_shuffled);
    self.is_readonly(data.is_readonly);
    self.is_system(data.is_system);
    self.pattern(data.pattern);
    self.decimal_places(data.decimpal_places);
    self.value_min(data.value_min);
    self.value_max(data.value_max);
    self.fields((data.fields || []).map(function(value){
      return new Field(value);
    }));
    self.choices((data.choices || []).map(function(value){
      return new Choice(value);
    }));
  };

  self.update(data);
}
