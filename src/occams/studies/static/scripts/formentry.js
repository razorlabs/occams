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

      // Load the specified version of the form
      $form.on('change', '[name="ofmetadata_-version"]', function(event){
        $.get(window.location, {'version': event.target.value}, function(data, textStatus, jqXHR){
          $form.children().not('.entity').remove();
          $form.append($(data).children());
        });
      });

      // Disable all fields if not done is checked
      $form.on('change', '[name="ofmetadata_-not_done"]', function(event){
        $('.ds-widget', $form).prop('disabled', event.target.checked);
      });

    });
  };

  $(function(){
    $('.js-formentry').formentry();
  });

}(jQuery);
