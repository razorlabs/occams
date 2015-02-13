function Visit(data){
  'use strict';

  var self = this;

  self.__url__ = ko.observable();
  self.id = ko.observable();
  self.visit_date = ko.observable();
  self.cycles = ko.observableArray();
  self.entities = ko.observableArray();

  self.include_forms = ko.observable(true);
  self.include_specimen = ko.observable(true);

  self.hasCycles = ko.pureComputed(function(){
    return self.cycles().length > 0;
  });

  self.hasEntities = ko.pureComputed(function(){
    return self.entities().length > 0;
  });

  self.update = function(data) {
    self.__url__(data.__url__);
    self.id(data.id);
    self.visit_date(data.visit_date);
    self.cycles((data.cycles || []).map(function(value){
      return new Cycle(value);
    }));
    self.entities(data.entities || []);
  };

  self.entitiesNotStartedCount = ko.pureComputed(function(){
    return self.entities().filter(function(entity){
      return entity.state.name == 'pending-entry';
    }).length;
  });

  self.entitiesNotStartedProgress = ko.pureComputed(function(){
    if (!self.hasEntities()){
      return 0;
    }
    return Math.round((self.entitiesNotStartedCount() / self.entities().length) * 100);
  });

  self.entitiesIncompleteCount = ko.pureComputed(function(){
    return self.entities().filter(function(entity){
      return entity.state.name != 'pending-entry'&& entity.state.name != 'complete';
    }).length;
  });

  self.entitiesIncompleteProgress = ko.pureComputed(function(){
    if (!self.hasEntities()){
      return 0;
    }
    return Math.round((self.entitiesIncompleteCount() / self.entities().length) * 100);
  });

  self.entitiesCompletedCount = ko.pureComputed(function(){
    return self.entities().filter(function(entity){
      return entity.state.name == 'complete';
    }).length;
  });

  self.entitiesCompletedProgress = ko.pureComputed(function(){
    if (self.entities().length < 1) {
      return 0;
    }
    return Math.round((self.entitiesCompletedCount() / self.entities().length) * 100);
  });

  self.toRest = function(){
    return {
      cycles: self.cycles().map(function(cycle){ return cycle.id(); }),
      visit_date: self.visit_date(),
      include_forms: self.include_forms(),
      include_specimen: self.include_specimen(),
    };
  };

  self.update(data || {});
}
