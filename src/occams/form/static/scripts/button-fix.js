/**
 * Button Fix
 *
 * Alters the behavior of a POST form's submit event to disable the "submit"
 * buttons when the form data is being sent to the server in order to
 * prevent certain click-happy users from constantly re-sending the form
 * data, resulting in data inconsistency and possibly corruption.
 *
 */
(function($){
    'use strict';
    $(document).ready(function(){
        $(document).delegate('form[method="post"]', 'submit', function(event){
            if ($(this).data('submitFix')){
                // Also, don't submit via other means if already submitting
                event.preventDefault();
            } else {
                // Disable the submit buttons so the user doesn't go click-happy
                $(this).data('submitFix', true);
            }
        });
    });
})(jQuery);