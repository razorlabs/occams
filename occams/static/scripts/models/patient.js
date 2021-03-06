function Patient(data){
  'use strict';

  var self = this;

  self.__url__ = ko.observable();
  self.id = ko.observable();
  self.pid = ko.observable();
  self.site = ko.observable();
  self.references = ko.observableArray();
  self.external_services = ko.observableArray()

  self.isNew = ko.pureComputed(function(){
    return !self.id();
  });

  self.hasReferences = ko.pureComputed(function(){
    return self.references().length > 0;
  });

  self.hasExternalServices = ko.pureComputed(function(){
    return self.external_services().length > 0;
  });

  self.update = function(data){
    data = data || {};
    self.__url__(data.__url__);
    self.id(data.id);
    self.pid(data.pid);
    self.site(data.site ? new Site(data.site) : null);
    self.references((data.references || []).map(function(datum){
      return new Reference(datum);
    }));
    // Do not use an observablt for external refereces since we're
    // not managing them from the patient view, we're rendering
    // the output of the configurations
    self.external_services(data.external_services || []);
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

  self.select2ParamsSite = function(term,  page){
    return {vocabulary: 'available_sites', term: term};
  };

  self.select2ResultsSite = function(data, page, query){
    return {
      results: data.sites.map(function(value){
        return new Site(value);
      })
    };
  };

  self.select2ParamsReferenceType = function(term, page){
    return {vocabulary: 'available_reference_types', term: term};
  };

  self.select2ResultsReferenceType = function(data, page, query){
    return {
      results: data.reference_types.map(function(value){
        return new ReferenceType(value);
      })
    };
  };

  self.toRest = function(){
    return {
      site: self.site().id,
      references: self.references().map(function(reference){
        return reference.toRest();
      })
    };
  };

  self.update(data);
}
