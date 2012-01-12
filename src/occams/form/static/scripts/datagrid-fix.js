(function($){
    'use strict';
    // Run datagridfield's setup, since it assumes the DOM was
    // already there, but it's not because we dynamically load it.
    // Also fix it so that it triggers when the actual input
    // element is changed.
    $(document).ready(function(){
        $(document).delegate('.auto-append > .datagridwidget-cell input', 'change',
            function(event){
                dataGridField2Functions.autoInsertRow.call(this, event);
            }
        );
    });
})(jQuery);