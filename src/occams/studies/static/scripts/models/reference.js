/**
 * Client-side Reference Model
 */
function Reference(data){
  var self = this;

  self.__src__ = ko.observable();

  self.id = ko.observable();
  self.name = ko.observable();
  // reftype
  self.title = ko.observable();

  // Utilities

  self.isNew = ko.computed(function(){
    return !self.id();
  });

  /**
   * Update instance properties
   */
  self.update = function(data){
    ko.mapping.fromJS(data, {}, self);
  };

  /**
   * Serializes object for transport to server
   */
  self.toJS = function(){
    return ko.mapping.toJS(self, {
      include: ['id', 'name', 'title']
    });
  };

  // Apply initial data
  self.update(data);
}
