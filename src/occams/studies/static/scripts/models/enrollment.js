/**
 * Client-side Enrollment Model
 */
function Enrollment(data){
  var self = this;

  self.__src__ = ko.observable();        // Data source

  // Database columns

  self.id = ko.observable();
  self.consent_date = ko.observable();
  self.latest_consent_date = ko.observable();
  self.termination_date = ko.observable();
  self.reference_number = ko.observable();
  self.create_date = ko.observable();
  self.create_user = ko.observable();
  self.modify_date = ko.observable();
  self.modify_user = ko.observable();

  //  Database relations

  self.study = ko.observable();
  self.stratum = ko.observable();

  // Utilities

  self.isNew = ko.computed(function(){
    return !self.id();
  });

  self.isRandomized = ko.computed(function(){
    return !!self.stratum();
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
      include: ['id', 'pid', 'nurse', 'is_archived']
    });
  };

  // Apply initial data
  self.update(data);
}
