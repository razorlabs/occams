function ReferenceType(data){
  'use strict';

  var self = this;

  self.name = ko.observable();
  self.title = ko.observable();
  self.description = ko.observable();

  self.reference_pattern = ko.observable();
  self.reference_hint = ko.observable();

  self.update = function(data){
    ko.mapping.fromJS(data, {}, self);
  };

  self.toJS = function(){
    return ko.toJS(self);
  };

  self.update(data);
}
