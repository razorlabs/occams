function Visit(data){
  var self = this;

  self.visit_date = ko.observable();
  self.cycles = ko.observableArray();
  self.entities = ko.observableArray();

  self.hasCycles = ko.pureComputed(function(){
    return self.visits().length > 0;
  });

  self.hasEntities = ko.pureComputed(function(){
    return self.entities().length > 0;
  });

  self.update = function(data) {
    ko.mapping.fromJS(data, {}, self);
  };

  self.entitiesNotStartedCount = ko.computed(function(){
    return self.entities().filter(function(entity){
      return entity.state.name() == 'pending-entry';
    }).length;
  });

  self.entitiesNotStartedProgress = ko.computed(function(){
    if (!self.hasEntities()){
      return 0;
    }
    return Math.round((self.entitiesNotStartedCount() / self.entities().length) * 100);
  });

  self.entitiesIncompleteCount = ko.computed(function(){
    return self.entities().filter(function(entity){
      return entity.state.name() != 'pending-entry'&& entity.state.name() != 'complete';
    }).length;
  });

  self.entitiesIncompleteProgress = ko.computed(function(){
    if (!self.hasEntities()){
      return 0;
    }
    return Math.round((self.entitiesIncompleteCount() / self.entities().length) * 100);
  });

  self.entitiesCompletedCount = ko.computed(function(){
    return self.entities().filter(function(entity){
      return entity.state.name() == 'complete';
    }).length;
  });

  self.entitiesCompletedProgress = ko.computed(function(){
    if (self.entities().length < 1) {
      return 0;
    }
    return Math.round((self.entitiesCompletedCount() / self.entities().length) * 100);
  });

  self.update(data);
}
