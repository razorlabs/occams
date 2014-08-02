/**
 * Applies validation via HTML5 attribuets
 */
+function($){

  $.fn.validation = function(options){

    var settings = $.extend({
        container: '.form-group',
        errorsContainer: '.form-errors',
        csrfCookieName: 'csrf_token',
        error: null,
        errorClass: 'has-error',
        remoteKey: 'validation_errors',
        remoteValidatingClass: 'js-validating',
      }, options )
      ;

    function updateMessages(element, messages){
      console.log(messages);
    }

    function checkRequired(element){
      var $e = $(element)
        , value = $e.val();
      if (($e.attr('required') || $e.data('required')) && !value){
        updateMessages($e, $e.data('required-msg') || 'Input required');
        return false;
      }
      return true;
    }

    function checkMin(element){
      var $e = $(element)
        , req = $e.attr('min') || $e.data('min')
        , value = $e.val();
      if (req > -1 && req >= value){
        updateMessages($e, $e.data('min-msg') || 'Must be greater than ' + req);
        return false
      }
      return true;
    }

    function checkMax(element){
      var $e = $(element)
        , req = $e.attr('max') || $e.data('max')
        , value = $e.val();
      if (req > -1 && req <= value) {
        updateMessages($e, $e.data('max-msg') || 'Must be less than ' + req);
        return false;
      }
      return true;
    }

    function checkMinLength(element){
      var $e = $(element)
        , req = $e.attr('minlength') || $e.data('minlength')
        , value = $e.val();
      if (req > -1 && req >= value.length){
        updateMessages($e, $e.data('minlength-msg') || 'Too short');
        return false;
      }
      return true;
    }

    function checkMaxLength(element){
      var $e = $(element)
        , req = $e.attr('maxlength') || $e.data('maxlength')
        , value = $e.val();
      req = $e.attr('maxlength') || $e.data('maxlength');
      if (req > -1 && req <= value.length){
        updateMessages($e, $e.data('maxlength-msg') || 'Too long');
        return false;
      }
      return true;
    }

    function checkPattern(element){
      var $e = $(element)
        , req = $e.attr('pattern') || $e.data('pattern')
        , value = $e.val();
      if (req && !new RegExp(req).test(value)){
        updateMessages($e, $e.data('pattern-msg') || 'Invalid pattern');
        return false;
      }
      return true;
    }

    function checkRemote(element){
      var $e = $(element)
        , req = $e.data('remote')
        , value = $e.val();
      if (req){
        $(e).closest(settings.containerElement).addClass(settings.remoteValidatingClass);
        var data = {}
        data[$(e).attr('name')] = value;
        $.ajax({
          url: req,
          method: 'POST',
          data: data,
          headers: {'X-CSRF-Token': $.cookie(settings.csrfCookieName)},
          error: function(jqXHR, textStatus, errorThrown){
            var data = jqXHR.responseJSON;
            if (!data){
              alert('Unable to communicate with server');
              return;
            }
            updateMessages(data[settings.remoteKey]);
          },
          complete: function(){
            $(e).closest(settings.containerElement).remoteClass(settings.remoteValidatingClass);
          }
        });
        return true;
      }
    }

    return this.each(function() {
      $('input,textarea,select', this)
        .on('focusout', function(event){
          var chain =  checkRequired(this)
                    && checkMin(this)
                    && checkMax(this)
                    && checkMinLength(this)
                    && checkMaxLength(this)
                    && checkPattern(this)
                    && checkRemote(this);
          return this;
        });
    });
  }

}(jQuery);
