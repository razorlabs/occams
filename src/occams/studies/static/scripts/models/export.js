/**
 * An individual Export model
 */
function Export(data) {
  var self = this;

  ko.mapping.fromJS(data,  {
      // select only the items we want to observe
      observe: ['status', 'count', 'total', 'file_size']
  }, self);

  /**
   * Calculates this export's current progress
   */
  self.progress = ko.computed(function(){
    return (self.count() / self.total()) * 100;
  }).extend({ throttle: 1 });
}
