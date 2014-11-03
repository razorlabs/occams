function Site(data){
  'use strict';

  var self = this;

  self.name = ko.observable();
  self.title = ko.observable();

  self.update = function(data){
    ko.mapping.fromJS(data, {}, self);
  };

  self.toJS = function(){
    return ko.toJS(self);
  };

  self.update(data);
}
