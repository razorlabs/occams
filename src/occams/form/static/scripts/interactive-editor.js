(function($){
    'use strict';
    
    $(document).ready(function(){
        $('#occams-form-fieldsets').sortable({
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
            containment: '#occams-form-editor',
            cursor: 'move',
            helper: 'clone',
            revert: true,
            start: function(event, ui){
                console.log($(this).width());
                $(ui.helper).width( $(this).width() );
            },
        });

        
        $('.occams-form-fieldset > .occams-form-metadata .occams-form-edit').click(function(event){
            event.preventDefault();
            console.log('fieldset modified')
        });
        
        $('.occams-form-fieldset > .occams-form-metadata .occams-form-delete').click(function(event){
            event.preventDefault();
            console.log('fieldset deleted');
        });
        
        $('.occams-form-field .occams-form-edit').click(function(event){
            event.preventDefault();

            var fieldElement = $(this).parents('.occams-form-field');
            var widgetElement = fieldElement.find('.occams-form-widget');
            console.log($(this));
            console.log('adfasfasfsad');
            console.log(fieldElement);
            console.log('wtf??');
            console.log(widgetElement);
            widgetElement.load($(this).attr('href') + ' #form')
            
        });
        
        $('.occams-form-field .occams-form-delete').click(function(event){
            event.preventDefault();
            $.ajax({
                url: '/Plone/testing/fia-forms-1/LumbarPuncture/test_source/@@test',
                success: function (data){
                    console.log(data);
                },
            })
        });
        
    });

})(jQuery);
