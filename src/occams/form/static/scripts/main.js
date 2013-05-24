(function($){
  'use strict';

  /**
   * Modal window controller
   */
  var Modal = {

      init: function() {
        $(document.body).append('<div id="modal" class="modal hide" data-backrop="status"></div>');
        $(document.body).on('click', '.overlay', Modal.onOverlayClick);
        $('#modal').on('click', 'button[name="cancel"]', Modal.onCancelClick);
        $('#modal').on('click', 'button[type="submit"]', Modal.onSubmitClick);
      },

      onOverlayClick: function(event) {
        event.preventDefault();
        console.log('asdfasfsadf');
        $('#modal').load(event.target.href, Modal.onPanelLoad);
      },

      onCancelClick: function(event){
        event.preventDefault();
        $('#modal').modal('hide').empty();
      },

      onSubmitClick: function(event) {
        event.preventDefault();

        var button = $(event.currentTarget);
        var form = $(button.prop('form'));
        var data = form.serializeArray();

        data.push({name: button.attr('name'), value: button.val()});

        $.ajax({
          type: form.attr('method'),
          url: form.attr('action'),
          data: data,
          statusCode: {
            200: Modal.onFormSuccess,
            302: Modal.onFormSuccess,
            400: Modal.onFormError,
          }
        });
      },

      onFormError: function(xhr, status, error){
        $('#modal').html(xhr.responseText);
      },

      onFormSuccess: function(text, status, xhr) {
        $('#modal').modal('hide').empty();
      },

      onPanelLoad: function(text, status, xhr) {
        $('#modal').modal('show');
      }

    };

  /* Initialize services */
  $(document).ready(Modal.init);

})(jQuery);
