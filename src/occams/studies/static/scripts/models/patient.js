function Patient(data){
  'use strict';

  var self = this;

  self.__url__ = ko.observable();
  self.id = ko.observable();
  self.pid = ko.observable();
  self.site = ko.observable();
  self.references = ko.observableArray();

  self.hasReferences = ko.pureComputed(function(){
    return self.references().length > 0;
  });

  self.update = function(data){
    self.__url__(data.__url__);
    self.id(data.id);
    self.pid(data.pid);
    self.site(data.site ? new Site(data.site) : null);
    self.references((data.references || []).map(function(value){
      return new Reference(value);
    }));
    self.references.sort(function(a, b){
      return a.reference_type().title().localeCompare(b.reference_type().title());
    });
  };

  self.deleteReference = function(reference){
    self.references.remove(reference);
  };

  self.addReference = function(){
    self.references.push(new Reference());
  };

  self.update(data || {});
}
