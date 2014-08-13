/**
 * Client-side ReferenceType Model
 */
function ReferenceType(data){
  var self = this;

  self.__src__ = ko.observable();
  self.id = ko.observable();
  self.name = ko.observable();
  self.title = ko.observable();

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

ReferenceType.availableOptions= ko.observableArray();
