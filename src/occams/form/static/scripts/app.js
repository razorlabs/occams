/**
 * Application
 */
(function($){
  'use strict';

  $(document).ready(function(){
    // Create the container and modalize it
    $('<div id="modal" class="modal hide"></div>')
        .appendTo(document.body)
        .modalize()
        .on('cancel', function(){ console.log('cancelled'); })
        .on('success', function(){ console.log('success'); });
  });

})(jQuery);

