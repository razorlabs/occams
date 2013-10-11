+function($){
  'use strict';

  $(document).ready(function(){

    // Only execute in specific views
    if ( !$('#data_list, #data_download').length ){
      return;
    }

    var socket = io.connect('/export');

    socket.on('progress', function(msg){
      console.log(msg)
    });

    socket.on('done', function(){
    });

    socket.on('error', function(msg){
      console.log(msg)
    });

  });

}(jQuery);
