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
    self.reference_type(data.reference_type ? new ReferenceType(data.reference_type) : null);
    self.reference_number(data.reference_number);
  };

  self.update(data || {});
}
