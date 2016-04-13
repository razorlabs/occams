function ExternalService(data){
  'use strict';

  var self = this;

  self.__url__ = ko.observable();

  self.id = ko.observable();
  self.name = ko.observable();
  self.title = ko.observable();
  self.description = ko.observable();
  self.url_template = ko.observable();

  self.isNew = ko.pureComputed(function(){
    return !self.id();
  });

  self.update = function(data){
    data = data || {};
    self.__url__(data.__url__);
    self.id(data.id);
    self.name(data.name);
    self.title(data.title);
    self.description(data.description);
    self.url_template(data.url_template);
  };

  self.update(data);
}
