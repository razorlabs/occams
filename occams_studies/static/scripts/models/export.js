/**
 * An individual Export model
 */
function Export(data) {
  'use strict';

  var self = this;

  self.update = function(data){
    // TODO need to formally declare values here
    self.count(data.count);
    self.total(data.total);
  };

  /**
   * Calculates this export's current progress
   */
  self.progress = ko.pureComputed(function(){
    return Math.ceil((self.count() / self.total()) * 100);
  }).extend({ throttle: 1 });

  self.update(data || {});
}

