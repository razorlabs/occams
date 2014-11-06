/**
 * Miscallaneous modal tools
 */
+function($){
  'use strict';

  ko.bindingHandlers.showModal = {
    update: function (element, valueAccessor) {
      $(element).modal(ko.unwrap(valueAccessor()) ? 'show' : 'hide');
    }
  };

}(jQuery);
