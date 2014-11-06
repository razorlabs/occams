function Version(data) {
  'use strict';

  var self = this;

  self.__src__ = ko.observable();
  self.id = ko.observable();
  self.publish_date = ko.observable();
  self.retract_date = ko.observable();

  self.isNew = ko.pureComputed(function(){ return !self.id(); });

  self.update = function(data){
    data = data || {};
    self.__src__(data.__src__);
    self.id(data.id);
    self.publish_date(data.publish_date);
    self.retract_date(data.retract_date);
  };

  self.update(data);
}
