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
    data = data || {};
    self.__url__(data.__url__);
    self.id(data.id);
    self.visit_date(data.visit_date);
    self.cycles((data.cycles || []).map(function(value){
      return new Cycle(value);
    }));
    self.entities((data.entities || []).map(function(value){
      return new Entity(value);
    }));
  };

  self.progress = ko.pureComputed(function(){
    var states = {
          'complete': {'order': 0, 'css': 'progress-bar progress-bar-success'},
          'pending-correction': {'order': 1, 'css': 'progress-bar progress-bar-primary'},
          'pending-review': {'order': 2,  'css': 'progress-bar progress-bar-warning'},
          'in-progress': {'order': 3,  'css': 'progress-bar progress-bar-info'},
          'pending-entry': {'order': 4, 'css': 'progress-bar progress-bar-danger'}
        },
        grouped = groupBy(self.entities(), function(e){
          return e.state().name;
        }),
        mapped = grouped.map(function(items){
          var state = items[0].state();
          return {
            'state': state,
            'css': states[state.name].css,
            'order': states[state.name].order,
            'count': items.length,
            'percent': ((items.length / self.entities().length) * 100).toFixed(1)
          };
        }),
        result = mapped.sort(function(a, b){
          return a.order - b.order;
        });

    return result;
  });

  self.toRest = function(){
    return {
      cycles: self.cycles().map(function(cycle){ return cycle.id(); }),
      visit_date: self.visit_date(),
      include_forms: self.include_forms(),
      include_specimen: self.include_specimen(),
    };
  };

  self.update(data);
}
