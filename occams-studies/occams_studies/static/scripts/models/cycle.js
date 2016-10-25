/**
 * Cycle representation in the context of a study
 */
function Cycle(data){
  'use strict';

  var self = this;

  self.__url__ = ko.observable();
  self.id = ko.observable();
  self.name = ko.observable();
  self.title = ko.observable();
  self.week = ko.observable();
  self.is_interim = ko.observable();
  self.forms = ko.observableArray();

  self.update = function(data){
    self.__url__(data.__url__);
    self.id(data.id);
    self.name(data.name);
    self.title(data.title);
    self.week(data.week);
    self.is_interim(data.is_interim);
    self.forms((data.forms || []).map(function(value){
      return new StudyForm(value);
    }));
  };

  self.hasForms = ko.pureComputed(function(){
    return self.forms().length;
  });

  self.formsIndex = ko.pureComputed(function(){
    var set = {};
    self.forms().forEach(function(form){
      set[form.schema().name] = true
    });
    return set;
  });

  self.containsForm = function(form){
    return form.schema().name in self.formsIndex();
  };

  self.update(data || {});
}
