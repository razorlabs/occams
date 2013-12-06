/**
 * Listens for export notifications and updates the page progress bars.
 */
+function($){
  'use strict';

  $(document).ready(function(){

    // Only execute in specific views
    if ( !$('#data_download').length ){
      return;
    }

    var socket = io.connect('/export');

    /**
     * Connects to the socket resource and registers listeners
     */
    socket.on('connect', function(){

      /**
       * Listens for progress noticiations.
       */
      socket.on('progress', function(data){
        var $panel = $('#export-' + data['export_id'])
          , progress = (data['count'] / data['total']) * 100
          , status = data['status'] ;


        // update the progress bar percentage
        $panel.find('.progress-bar').css({width: progress + '%'});
        $panel.find('.progress-bar .sr-only').text(progress + '%');

        // remove the progress bar if complete and enable the download link
        if (status == 'complete') {
          // TODO: need to i18n this.
          $panel.find('.panel-title .status').text('Complete');
          $panel.removeClass('panel-default').addClass('panel-success');
          $panel.find('.panel-body').remove();
          $panel.find('.panel-footer .btn-primary').removeClass('disabled');
        }
      });

      /**
       * Closes the conenction when the user is navigating away
       */
      $(window).on('beforeunload', function(){
        socket.disconnect();
      });

    });

  });

}(jQuery);
