/**
 * Client-side Patient Model
 */
function Patient(data){
  var self = this;

  self.__src__ = ko.observable();        // Data source

  // Database columns

  self.id = ko.observable();
  self.site_id = ko.observable();
  self.site = ko.computed(function(){
    return ko.utils.arrayFirst(Site.availableOptions(), function(site){
      return site.id() === self.site_id();
    });
  });
  self.pid = ko.observable();
  self.nurse = ko.observable();
  self.is_archived = ko.observable();
  self.create_date = ko.observable();
  self.create_user = ko.observable();
  self.modify_date = ko.observable();
  self.modify_user = ko.observable();

  //  Database relations

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

  self.addReference = function(){
    self.references.push(new Reference());
  }

  self.deleteReference = function(item){
    self.references.remove(item);
  }

  /**
   * Update instance properties
   */
  self.update = function(data){
    if (!data){
      return;
    }
    ko.mapping.fromJS(data, {
      references: {
        key: function(item){
          return ko.utils.unwrapObservable(item.id);
        },
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

  // Apply initial data
  self.update(data);
}
