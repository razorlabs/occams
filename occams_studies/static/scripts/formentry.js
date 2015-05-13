+function($){
  'use strict';

  /**
   * Datastore client-side data entry behaviors
   */
  $.fn.formentry = function(){
    return this.each(function(){
      var $form = $(this);

      // Enable validation
      $form.validate()

      // Enable widgets
      $('.js-select2:not([data-bind])').each(function(i, element){
        // select2 doesn't check if already initialized...
        if ($(element).data('select2') === undefined){
          $(element).select2();
        }
      });

      $('input[type=date]:not([data-bind]),.js-date:not([data-bind])').datetimepicker({pickTime: false});
      $('input[type=datetime]:not([data-bind]),.js-datetime:not([data-bind])').datetimepicker();

      // Load the specified version of the form
      $form.on('change', '[name="ofmetadata_-version"]', function(event){
        $.get(window.location, {'version': event.target.value}, function(data, textStatus, jqXHR){
          $form.children().not('.entity').remove();
          $form.append($(data).children());
        });
      });

      // Disable all fields if not done is checked
      $form.on('change', '[name="ofmetadata_-not_done"]', function(event){
        $form.validate().resetForm();
        $('.form-group', $form).removeClass('alert alert-danger has-error');
        $('.errors').remove();
        $('.ds-widget', $form).prop('disabled', event.target.checked);
      });

    });
  };

  $(function(){
    $('.js-formentry').formentry();
  });

  ko.bindingHandlers.formentry = {
    init: function(element, valueAccessor, allBindingsAccessor) {
      $(element).formentry();
    }
  };

}(jQuery);
