function Form(data) {
  'use strict';

  var self = this;

  self.name = ko.observable();
  self.title = ko.observable();
  self.has_private = ko.observable();
  self.versions = ko.observableArray();

  self.isNew = ko.pureComputed(function(){ return !self.hasVersions(); });

  self.hasVersions = ko.pureComputed(function(){
    return self.versions().length > 0
  });

  self.update = function(data){
    data = data || {};
    self.name(data.name);
    self.title(data.title);
    self.has_private(data.has_private);
    self.versions((data.versions || []).map(function(value){
      return new Version(value);
    }));
  };

  self.update(data);
}
