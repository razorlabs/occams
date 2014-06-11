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
        201: function(data, status, xhr) {
          var location = xhr.getResponseHeader('Location');
          if (location) {
            window.location = location
            return;
          }
          $this.toggle('hide');
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
    $(this).empty();
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

}(jQuery);
