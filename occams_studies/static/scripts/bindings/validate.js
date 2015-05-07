/**
 * Validation tools
 */

+function($){
  'use strict';

  /**
   * Binds a form element to use jQuery validation tools
   * The argument should be a an object of settings.
   */
  ko.bindingHandlers.validate = {
    init: function (element, valueAccessor) {
      $(element).validate(ko.unwrap(valueAccessor()));
    },
  };

  $.validator.setDefaults({
    errorClass: 'has-error',    // use bootstrap's classes to indicate invalid
    validClass: 'has-success',  // use bootstrap's classes to indicate valid
    wrapper: 'p',
    // Ignore helper form elements
    ignore: '.select2-input, .select2-focusser',
    errorPlacement: function(error, element){
      error.addClass('help-block');
      var $container = $(element).closest('.form-group').find('.errors').append(error);
      if ($container.length < 1){
        console.warn('Could not find closest ".form-group > .errors" for validation of:', element);
        $(error).insertAfter(element);
      }
    },
    onfocusout: function(element, event){
      // validate, but wait half a moment otherwise we might interrupt
      // something else the user intended on clicking on, such as cancel
      var delay = 500; // just barely enough to click on something else
      window.setTimeout(function(){$(element).valid();}, delay);
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
  });

 // Copied the following form additional methods since all I need is pattern.
 /**
  * Return true if the field value matches the given format RegExp
  *
  * @example $.validator.methods.pattern('AR1004',element,/^AR\d{4}$/)
  * @result true
  *
  * @example $.validator.methods.pattern('BR1004',element,/^AR\d{4}$/)
  * @result false
  *
  * @name $.validator.methods.pattern
  * @type Boolean
  * @cat Plugins/Validate/Methods
  */
  $.validator.addMethod('pattern', function(value, element, param) {
    if (this.optional(element)) {
      return true;
    }
    if (typeof param === 'string') {
      param = new RegExp(param);
    }
    return param.test(value);
  }, $.validator.format('Invalid format.'));


  /**
   * Helper method to properly parse out values from form elements
   */
  var parseValue = function(element){
    var $element = $(element)
      , type = $element.data('type-hint')
      , value = $element.val();
    switch (type){
      case 'date':
      case 'datetime':
        return moment(value);
      case 'int':
      case 'integer':
        return parseInt(value);
      case 'decimal':
      case 'float':
        return parseFloat(value);
      default:
        return value;
    }
  };

  /**
   * Helper method that adds a listenr to other element to
   * revalidate this element when modified.
   */
  var listentOther = function(element, other){
    var $element = $(element)
      , $other = $(other)
      , uid = 'dependent-' + $element.attr('name') + '-' + $other.attr('name');
    // Only configure once
    if (!$element.data(uid)){
      $other.on('focusout', function(){
        $($element.closest('form')).validate().element(element);
      });
      $element.data(uid, {});
    }
  };

  /**
   * Ensures the current element is less than the target element
   */
  $.validator.addMethod('lessThan', function(value, element, param){
    if (this.optional(element)){
      return true;
    }
    var $param = $(param)
      , value = parseValue(element)
      , other = parseValue($param);
    listentOther(element, $param);
    return other && value < other;
  }, $.validator.format('Not less than {0}'));

  /**
   * Ensures the current element is less than or equal to the target element
   */
  $.validator.addMethod('lessThanEqualTo', function(value, element, param){
    if (this.optional(element)){
      return true;
    }
    var $param = $(param)
      , value = parseValue(element)
      , other = parseValue($param);
    listentOther(element, $param);
    return other && value <= other;
  }, $.validator.format('Not less than or equal to {0}'));

  /**
   * Ensures the current element is greater than the target element
   */
  $.validator.addMethod('greaterThan', function(value, element, param){
    if (this.optional(element)){
      return true;
    }
    var $param = $(param)
      , value = parseValue(element)
      , other = parseValue($param);
    listentOther(element, $param);
    return other && value > other;
  }, $.validator.format('Not less than {0}'));

  /**
   * Ensures the current element is greater than or equal to the target element
   */
  $.validator.addMethod('greaterThanEqualTo', function(value, element, param){
    if (this.optional(element)){
      return true;
    }
    var $param = $(param)
      , value = parseValue(element)
      , other = parseValue($param);
    listentOther(element, $param);
    return other && value >= other;
  }, $.validator.format('Not less than or equal to {0}'));

}(jQuery);
