/**
 * Validation tools
 */
+function($){
  'use strict';

  ko.bindingHandlers.validate = {
    init: function (element, valueAccessor) {
      $(element).validate(ko.utils.unwrapObservable(valueAccessor()));
    },
  };

}(jQuery);


// Valiation options that accommodate Bootstrap styling
var defaultValidationOptions = {
    errorClass: 'has-error',
    validClass: 'has-success',
    wrapper: 'p',
    errorPlacement: function(label, element){
      label.addClass('help-block').insertAfter(element);
    },
    onfocusout: function(element, event){
      $(element).valid();
    },
    highlight: function(element, errorClass, validClass){
      $(element)
        .closest('.js-validation-item,.form-group')
        .addClass(errorClass)
        .removeClass(validClass);
    },
    unhighlight: function(element, errorClass, validClass){
      $(element)
        .closest('.js-validation-item,.form-group')
        .addClass(validClass)
        .removeClass(errorClass);
    }
};


+function($){
 // Copied the following form additional methods since all I need is pattern.
 /**
  * Return true if the field value matches the given format RegExp
  *
  * @example $.validator.methods.pattern("AR1004",element,/^AR\d{4}$/)
  * @result true
  *
  * @example $.validator.methods.pattern("BR1004",element,/^AR\d{4}$/)
  * @result false
  *
  * @name $.validator.methods.pattern
  * @type Boolean
  * @cat Plugins/Validate/Methods
  */
  $.validator.addMethod("pattern", function(value, element, param) {
    if (this.optional(element)) {
      return true;
    }
    if (typeof param === "string") {
      param = new RegExp(param);
    }
    return param.test(value);
  }, "Invalid format.");
}(jQuery);
