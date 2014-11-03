function Patient(data){
  'use strict';

  var self = this;

  self.pid = ko.observable();
  self.site = ko.observable();
  self.references = ko.observableArray();

  self.hasReferences = ko.pureComputed(function(){
    return self.references().length > 0;
  });

  self.update = function(data){
    ko.mapping.fromJS(data, {
      'references': {
        'create': function(options){
          return new Reference(options.data);
        }
      }
    }, self);
  };

  self.deleteReference = function(reference){
    self.references.remove(reference);
  };

  self.addReference = function(){
    self.references.push(new Reference());
  };

  self.toJS = function(){
    return ko.toJS(self);
  }

  self.update(data);
}
