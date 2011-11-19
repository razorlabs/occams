(function($){
    'use strict';
    
    $(document).ready(function(){
        $('#occams-form-subforms').sortable({
            axis: 'y',
            containment: 'parent',
            forcePlaceholderSize: true,
            // intersect won't work for sub-forms since they can be huge
            opacity: 0.6,
        });
        
        $('.occams-form-fields').sortable({
            axis: 'y',
            connectWith: '.occams-form-fields',
            forcePlaceholderSize: true,
            tolerance: 'intersect',
            opacity: 0.6,
        });
        
        
        $('#occams-form-types > ul > li').draggable({
//            containment: '#occams-form-editor',
            cursor: 'move',
            helper: 'clone',
            revert: true,
            start: function(event, ui){
                console.log($(this).width());
                $(ui.helper).width( $(this).width() );
            },
        });
        
        $('.occams-form-field-navigation .delete').click(function(event){
            event.preventDefault();
        });
        
        $('.occams-form-field-navigation .edit').click(function(event){
            event.preventDefault();
            var parent = $(this).parents('.occams-form-field');
            parent.find('.occams-form-field-widget').hide('slow');
            parent.find('.occams-form-field-navigation').hide('slow');
            
        });
        
    });

})(jQuery);
