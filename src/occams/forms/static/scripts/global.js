/**
 * Global settings
 */

var html5 = {inputtypes: {}};

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
        .closest('.js-validation-group,.form-group')
        .addClass(errorClass)
        .removeClass(validClass);
    },
    unhighlight: function(element, errorClass, validClass){
      $(element)
        .closest('.js-validation-group,.form-group')
        .addClass(validClass)
        .removeClass(errorClass);
    }
}

+function(){
  // Checks if an input type is supported
  // Could have used Modernizr, but consider 15Kb vs 15 lines...
  var check = function(type){
    var i = document.createElement('input');
    i.setAttribute('type', type);
    return i.type !== 'text';
  };
  var htmltypes = [
    'color', 'date', 'datetime', 'datetime-local', 'email', 'month',
    'number', 'range', 'search', 'tel', 'time', 'url', 'week'];

  $.each(htmltypes, function(i, e){
    window.html5.inputtypes[e] = check(e);
  });
}();

$(document).ready(function(){
  $('js-select2').select2();
  if (!html5.inputtypes.datetime){
    $('.js-datetimepicker').datetimepicker();
  }
  if (!html5.inputtypes.date){
    $('.js-datepicker').datetimepicker({pickTime: false});
  }
});
