/**
 * An individual Export model
 */
function Export(data) {
  var self = this;

  ko.mapping.fromJS(data, {}, self);

  /**
   * Calculates this export's current progress
   */
  self.progress = ko.computed(function(){
    return (self.count() / self.total()) * 100;
  }).extend({ throttle: 1 });
}

