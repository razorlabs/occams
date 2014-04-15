/**
 * Miscallaneous modal tools
 */
+function($){
  'use strict';

  /**
   * Basic handler for sending form data via ajax until it's successful
   */
  $('#modal').on('submit', function(event){
    event.preventDefault();

    var $this = $(this)
      , $form = $(event.target);

    $.ajax({
      type: $form.attr('method'),
      url: $form.attr('action'),
      data: $form.serialize(),
      statusCode: {
        200: function(data, status, xhr) {
          var location = xhr.getResponseHeader('Location');
          if (location) {
            window.location = location
            return;
          }
          $this.modal('hide');
        },
        400: function(xhr, status, error) {
          $this.html(xhr.responseText)
        }
      }
    });
  });


  /**
   * Clears modal container contents.
   */
  $('#modal').on('hidden.bs.modal', function(){
    $(this).find('.modal-content').empty();
    // Ensure the remote content can be reloaded
    $(this).removeData('bs.modal');
    return this;
  });


  /**
   * Allows buttons inside the modal to be able to close it.
   */
  $('#modal').on('click', '.js-modal-dismiss', function(event){
    event.preventDefault();
    return $('#modal').modal('hide');
  });

  // http://stackoverflow.com/q/14683953/148781
  ko.bindingHandlers.showModal = {
    init: function (element, valueAccessor) { },
    update: function (element, valueAccessor) {
      var value = valueAccessor();
      if (ko.utils.unwrapObservable(value)) {
        $(element).modal('show');
        // this is to focus input field inside dialog
        $('input', element).focus();
      } else {
        $(element).modal('hide');
      }
    }
  };

}(jQuery);
