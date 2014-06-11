+function($) {
  "use strict";

  $(document).ready(function(){

    if ($('#export_faq').length < 1){
      return;
    }

    $('body').scrollspy({target: '#export-faq-sidebar' })

    $('#export-faq-sidebar').affix({
      offset: { top: $('#export-faq-sidebar').parent().offset().top }
    });

    $(window).resize(function(){
      $('#export-faq-sidebar').width(function(index, width){
        return $(this).parent().width();
      });
    });

    $(window).resize();

  });
}(jQuery);
