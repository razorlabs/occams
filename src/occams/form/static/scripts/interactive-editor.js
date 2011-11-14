(function($){
    'use strict';
    
    $(document).ready(function(){
        
        $('#occams-form-fields').sortable({
            axis: 'y',
            containment: '#occams-form-fields',
            forcePlaceholderSize: true,
            tolerance: 'intersect',
            opacity: 0.6,
        });
        
        $("#occams-form-fields").droppable({
            accept: '#occams-form-types li',
            drop: function(event, ui) { 
                console.log('dropped');
                console.log(event);
                console.log(ui);
                console.log($(this))
            }
          });
        
        $('#occams-form-types > li').draggable({
            containment: '#occams-form-editor',
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
