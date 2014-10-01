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

+function(){
  /**
   * Check if the browser supports (and can actually validate) dates
   */
  var supportsDateInput = (function() {
    var input = document.createElement('input');
    input.setAttribute('type','date');
    var notADateValue = 'not-a-date';
    input.setAttribute('value', notADateValue);
    return !(input.value === notADateValue);
  })();

  /**
   * Enables a datetime picker widget for the input element
   */
  ko.bindingHandlers.datetimePicker = {
    init: function(element, valueAccessor, allBindingsAccessor) {
      if (!supportsDateInput) {
        $(element).datetimepicker(ko.unwrap(valueAccessor()));
      }
    }
  };
}();
