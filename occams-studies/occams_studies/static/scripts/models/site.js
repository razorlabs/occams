function Site(data){
  'use strict';

  var self = this;

  self.__url__ = ko.observable();
  self.id = ko.observable();
  self.name = ko.observable();
  self.title = ko.observable();

  self.update = function(data){
    self.__url__(data.__url__);
    self.id(data.id);
    self.name(data.name);
    self.title(data.title);
  };

  self.update(data || {});
}
