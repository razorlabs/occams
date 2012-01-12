(function($){
    'use strict';
    $(document).ready(function(){
        // Disable the submit button so the user doesn't go click-happy
        $(document).delegate('.formControls input', 'click', function(event){
            $(this).parent().find('input').each(function(){
                $(this).attr('disabled', 'disabled');
            });
        });
    });
})(jQuery);