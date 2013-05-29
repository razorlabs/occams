(function($){

  /**
   * Wraps Bootstrap's Modal plugin to dynamically load the ENTIRE
   * contents of the modal window.
   */
  $.fn.modalize = function(options) {

    var settings = $.extend({}, $.fn.modalize.defaults, options);

    /**
     * Handler for button triggers to launch the modal window
     */
    var onTriggerClick = function(event) {
      event.preventDefault();
      var href = $(event.currentTarget).attr('href');
      $(this).load(href, onLoad.bind(this));
    };

    /**
     * Cancels modal window and hides it
     */
    var onCancelClick = function(event){
      event.preventDefault();
      $(this).modal('hide');
    };

    /**
     * Sends form data to server
     */
    var onSubmitClick = function(event) {
      event.preventDefault();

      var button = $(event.currentTarget);
      var form = $(button.prop('form'));
      var data = form.serializeArray()
        .concat({name: button.attr('name'), value: button.val()});

      $.ajax({
        type: form.attr('method'),
        url: form.attr('action'),
        data: data,
        statusCode: {
          200: onFormSuccess.bind(this),
          302: onFormSuccess.bind(this),
          400: onFormError.bind(this),
        }
      });
    };

    /**
     * Re-renders form contents if there are errors
     */
    var onFormError = function(xhr, status, error){
      $(this).html(xhr.responseText);
      $(this).modal('show');
    };

    /**
     * Hides modal window after form has completed successfully
     */
    var onFormSuccess = function(text, status, xhr) {
      $(this).modal('hide');
    };

    /**
     * Displays loaded content in modal container
     */
    var onLoad = function(text, status, xhr) {
      $(this).modal('show');
    };

    /**
     * Empties the contents of the modal window after it's dissapeared
     */
    var onHidden = function() {
      $(this).empty();
    };

    /**
     * Adjusts modal body just before rendering it
     */
    var onShow = function() {
      var headerHeight = $('#modal .modal-header').height();
      var footerHeight = $('#modal .modal-footer').height();
      var windowHeight = $(window).height()
      var maxBodyHeight = windowHeight - (headerHeight + footerHeight);
      var $modal = $(this)
      var hasForm = $modal.find('form').length > 0;
      $modal.find('.modal-body').css('max-height', maxBodyHeight + 'px');
      $modal.data({
        keyboard: !hasForm,
        backdrop: hasForm ? 'static' : true
      });
    };

    /**
     * Constructor
     */
    return this.each(function() {
      var $modal = $(this);
      $(document).on('click', settings.trigger, onTriggerClick.bind(this));
      $modal.modal('hide');
      $modal.on('click', 'button[name="cancel"]', onCancelClick.bind(this));
      $modal.on('click', 'button[type="submit"]', onSubmitClick.bind(this));
      $modal.on('show', onShow.bind(this));
      $modal.on('hidden', onHidden.bind(this));
    });
  };

  $.fn.modalize.defaults = {
    trigger: '.modal-trigger',
  };

})(jQuery);
