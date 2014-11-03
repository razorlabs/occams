function Reference(data){
  'use strict';

  var self = this;

  self.reference_type = ko.observable();
  self.reference_number = ko.observable();

  self.reference_pattern = ko.pureComputed(function(){
    return self.reference_type() ? self.reference_type().reference_pattern() : null;
  });

  self.reference_hint = ko.pureComputed(function(){
    return self.reference_type() ? self.reference_type().reference_hint() : null;
  });

  self.update = function(data){
    ko.mapping.fromJS(data, {
      'reference_type': {
        'create': function(options){
          return options.data ? new ReferenceType(options.data) : null;
        }
      }
    }, self);
  };

  self.toJS = function(){
    return ko.toJS(self);
  };

  self.update(data);
}
