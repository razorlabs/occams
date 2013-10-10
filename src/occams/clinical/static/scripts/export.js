+function($){
  'use strict';

  $(document).ready(function(){

    if ( !$('#data_list, #data_download').length ){
      return;
    }

    var socket = io.connect('/export');

    socket.on('connect', function(){
      console.log('Connected!!!')
    });

    socket.on('hello', function(msg){
      console.log(msg)
    });

    $('form[name=export]').on('submit', function(event){
      event.preventDefault();
      socket.emit('wtf', 1234)
    });


  });

}(jQuery);
