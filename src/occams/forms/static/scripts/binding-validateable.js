/**
 * Annotates the observable with validation messages
 */
ko.extenders.validateable = function(target, overrides) {
    //add some sub-observables to our observable
    target.errors = ko.observableArray([]);

    target.hasErrors = ko.computed(function(){
      return target.errors().length > 0;
    });

    //return the original observable
    return target;
};


/**
 * Validation tools
 */
+function($){
  'use strict';

  ko.bindingHandlers.validation = {
    init: function (element, valueAccessor) {
      // Todo use valueAccessor as a settings object...
      $(element).validation();
    },
    update: function (element, valueAccessor) {
    }
  };

}(jQuery);
