+function(){
  "use strict";

  /**
   * Formats a value to a localized datetime string
   */
  ko.bindingHandlers.datetimeText = {
    update: function(element, valueAccessor, allBindingsAccessor) {
     var value = ko.unwrap(valueAccessor())
       , formattedValue = moment(value).format('llll');
      ko.bindingHandlers.text.update(element, function() { return formattedValue; });
    }
  };

  /**
   * Formats a value to a localized datet string
   */
  ko.bindingHandlers.dateText = {
    update: function(element, valueAccessor, allBindingsAccessor) {
     var value = ko.unwrap(valueAccessor())
       , formattedValue = moment(value).format('ll');
      ko.bindingHandlers.text.update(element, function() { return formattedValue; });
    }
  };

  /**
   * Enables a datetime picker widget for the input element
   */
  ko.bindingHandlers.datetimepicker = {
    init: function(element, valueAccessor, allBindingsAccessor) {
      $(element).datetimepicker(ko.unwrap(valueAccessor()));

      ko.utils.domNodeDisposal.addDisposeCallback(element, function() {
          $(element).data('DateTimePicker').destroy();
      });
    }
  };

}();
