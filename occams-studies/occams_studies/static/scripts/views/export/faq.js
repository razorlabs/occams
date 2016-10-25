function setup_exports_faq(){
  'use strict';

  if ($('#exports_faq').length < 0){
    return;
  }

  $('body').scrollspy({target: '#export-faq-sidebar' })

  $('#export-faq-sidebar').affix({
    offset: { top: $('#export-faq-sidebar').parent().offset().top }
  });

  $(window)
    .resize(function(){
      $('#export-faq-sidebar').width(function(index, width){
        return $(this).parent().width();
      });
    })
    .trigger('resize');
}
