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
          $this.toggle('hide').empty()
        },
        302: function(xhr, status, error) {
          window.location.href = xhr.getResponseHeader('Location');
        },
        400: function(xhr, status, error) {
          $this.html(data)
        }
      }
    });
  });

  /**
   * Allows buttons inside the modal to be able to close it.
   */
  $('#modal').on('click', '.js-close', function(event){
    event.preventDefault();
    return $(this).toggle('hide').empty()
  });

}(jQuery);
