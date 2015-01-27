function Version(data) {
  'use strict';

  var self = this;

  self.__url__ = ko.observable();
  self.id = ko.observable();
  self.name = ko.observable();
  self.title = ko.observable();
  self.description = ko.observable();
  self.publish_date = ko.observable();
  self.retract_date = ko.observable();

  self.fields = ko.observableArray();

  self.isNew = ko.pureComputed(function(){ return !self.id(); });

  self.hasFields = ko.pureComputed(function(){
    return self.fields().length > 0;
  });

  self.update = function(data){
    data = data || {};
    self.__url__(data.__url__);
    self.id(data.id);
    self.name(data.name);
    self.title(data.title);
    self.description(data.description);
    self.publish_date(data.publish_date);
    self.retract_date(data.retract_date);
    self.fields((data.fields || []).map(function(value){
      return new Field(value);
    }));
  };

  self.update(data);
}
