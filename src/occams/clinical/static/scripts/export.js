+function($){
  'use strict';

  $(document).ready(function(){

    // Only execute in specific views
    if ( !$('#data_download').length ){
      return;
    }

    var socket = io.connect('/export');

    socket.on('connect', function(){

      socket.on('progress', function(msg){
        console.log(msg);
      });

      $(window).on('beforeunload', function(){
        socket.disconnect();
      });

    });


  });

}(jQuery);
