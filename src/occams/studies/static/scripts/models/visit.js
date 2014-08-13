/**
 * Client-side Visit Model
 */
function Visit(data){
  var self = this;

  self.__src__ = ko.observable();        // Data source

  // Database columns

  self.id = ko.observable();
  self.visit_date = ko.observable()
  self.create_date = ko.observable();
  self.create_user = ko.observable();
  self.modify_date = ko.observable();
  self.modify_user = ko.observable();

  //  Database relations

  self.cycles = ko.observable();

  // Utilities

  self.num_complete = ko.observable();
  self.total_forms = ko.observable();

  self.progress = ko.computed(function(){
    if (self.total_forms() <= 0){
      return 0;
    }
    return Math.round((self.num_complete() / self.total_forms()) * 100);
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
      include: ['id', 'cycles', 'visit_date']
    });
  };

  // Apply initial data
  self.update(data);
}
