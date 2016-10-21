/**
 * Miscallaneous modal tools
 */
+function($){
  'use strict';

  ko.bindingHandlers.modalVisible = {
    update: function (element, valueAccessor) {
      var show = !!ko.unwrap(valueAccessor());
      $(element).modal(show ? 'show' : 'hide');
    }
  };

}(jQuery);
