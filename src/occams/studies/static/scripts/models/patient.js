/**
 * Client-side Patient Model
 */
function Patient(data){
  var self = this;

  self.__src__ = ko.observable();        // Data source

  // Database columns

  self.id = ko.observable();
  self.pid = ko.observable();
  self.nurse = ko.observable();
  self.is_archived = ko.observable();
  self.create_date = ko.observable();
  self.create_user = ko.observable();
  self.modify_date = ko.observable();
  self.modify_user = ko.observable();

  //  Database relations

  self.site = ko.observable();
  self.references = ko.observableArray();
  self.enrollments = ko.observableArray();
  self.visits = ko.observableArray();

  self.hasReferences = ko.computed(function(){
    return self.references().length > 0;
  });

  self.hasEnrollments = ko.computed(function(){
    return self.enrollments().length > 0;
  });

  self.hasVisits = ko.computed(function(){
    return self.visits().length > 0;
  });

  // Utilities

  self.isNew = ko.computed(function(){
    return !self.id();
  });

  /**
   * Update instance properties
   */
  self.update = function(data){
    ko.mapping.fromJS(data, {
      references: {
        create: function(options){
          return new Reference(options.data);
        }
      },
      enrollments: {
        create: function(options){
          return new Enrollment(options.data);
        }
      },
      visits: {
        create: function(options){
          return new Visit(options.data);
        }
      }
    }, self);
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

