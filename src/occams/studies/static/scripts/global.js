/**
 * Applicaiton-wide setup
 */
$(document).ready(function(){

  // Enable all tooltipes (bootstrap does not do this)
  $('[rel=tooltip]').tooltip();

  /**
   * Disable the submit buttons to prevent double-clicking
   */
  $('body').on('submit', function(event){
    var $buttons = $(event.target).find('button[type="submit"]');
    $buttons.prop('disabled', true);
    window.setTimeout(function(){ $buttons.prop('disabled', false); }, 10000);
  });

});
