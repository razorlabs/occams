/**
 * Re-usable error handler for XHR requests
 *
 * Options:
 *  logger -- (optional) the callback to forward the error message
 *            defaults to console.
 *  form -- (optional) the form element so handoff the server
 *          error validation messages.
 *
 * Returns a callable for use with jQuery's error option
 */
function handleXHRError(options){
  'use strict';

  var defaultLogger = function(msg){
    console.log(msg);
  };

  var logger = options.logger || defaultLogger,
      form = options.form;


  return function(jqXHR, textStatus, errorThrown){

    if (textStatus.indexOf('CSRF') > -1 ){
      // The session has expired and the user needs to be redirected
      window.location.reload();

    } else if (jqXHR.responseJSON){

      logger('Validation problems');

      if (form){
        $(form).validate().showErrors(jqXHR.responseJSON.errors);
      }

    } else if (!/<[a-z][\s\S]*>/i.test(jqXHR.responseText)){
      logger(jqXHR.responseText);

    } else {
      logger(errorThrown);

    }
  };
}
