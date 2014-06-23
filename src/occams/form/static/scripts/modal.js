/**
 * Miscallaneous modal tools
 */
+function($){
  'use strict';

  // http://stackoverflow.com/q/14683953/148781
  ko.bindingHandlers.showModal = {
    init: function (element, valueAccessor) { },
    update: function (element, valueAccessor) {
      var value = valueAccessor();
      if (ko.utils.unwrapObservable(value)) {
        $(element).modal('show');
        $('input', element).focus();
      } else {
        $(element).modal('hide');
      }
    }
  };

}(jQuery);
