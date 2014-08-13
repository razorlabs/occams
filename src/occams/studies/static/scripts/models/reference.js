/**
 * Client-side Reference Model
 */
function Reference(data){
  var self = this;

  self.__src__ = ko.observable();

  self.id = ko.observable();
  self.reference_type_id = ko.observable();
  self.reference_type = ko.computed(function(){
     return ko.utils.arrayFirst(ReferenceType.availableOptions(), function(type) {
      return type.id() === self.reference_type_id();
    });
  });
  self.reference_number = ko.observable();

  /**
   * Update instance properties
   */
  self.update = function(data){
    if (!data){
      return;
    }
    ko.mapping.fromJS(data, {}, self);
  };

  // Apply initial data
  self.update(data);
}
