(function($){
  'use strict';

  /**
   * Modal window service
   */
  var Modal = {
      init: function() {
        $(document.body).append('<div id="modal-container"></div>');
        $(document.body).on('click', '.overlay', Modal.onOverlayClick);
        $('#modal-container').on('submit', 'form', Modal.onSubmit);
        $('#modal-container').on('click', 'button[name="cancel"]', Modal.onCancelClick);
      },
      onOverlayClick: function(event) {
        event.preventDefault();
        var href = event.target.href + ' #modal';
        $('#modal-container').load(href, Modal.onPanelLoad);
      },
      onSubmit: function(event) {
        event.preventDefault();
        var form = $(event.target);
        var request = {
          type: form.prop('method'),
          url: form.prop('action'),
          data: form.serialize(),
          success: Modal.onFormSuccess
        };
        $.ajax(request);
      },
      onCancelClick: function(event) {
        event.preventDefault();
        $('#modal').modal('hide');
      },
      onFormSuccess: function(text, status, xhr) {
        if (xhr.status == 302) {
          $('#modal').modal('hide');
          return;
        }
        var contents = $(text).find('#modal');
        if (contents.length < 1) {
          alert('An error occurred while trying to load results');
          console.log(text);
          console.log(contents);
          return;
        }
        $('#modal-container').empty().append(contents);
      },
      onPanelLoad: function(text, status, xhr) {
        $('#modal').modal('show');
      }
    };

  /* Initialize services */
  $(document).ready(Modal.init);

})(jQuery);
