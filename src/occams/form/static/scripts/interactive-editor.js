/**
 * OCCAMS Form Editor Application 
 */
(function($){
    'use strict';
     
    /**
     * Main method that initializes all components
     */
    var main = function() {
        
        // Configure fieldsets as sortable within the editor, note that using
        // 'intersect' as a tolerance won't work here because the forms
        // can get rather huge and so it will look weird.
        $('#occams-form-fieldsets').sortable({
            axis: 'y',
            containment: 'parent',
            forcePlaceholderSize: true,
            opacity: 0.6,
        });
        
        // Configure fields as sortable within fieldsets (and across fieldsets)
        $('.occams-form-fields').sortable({
            axis: 'y',
            connectWith: '.occams-form-fields',
            forcePlaceholderSize: true,
            tolerance: 'intersect',
            opacity: 0.6,
        });
        
        // Configure types as draggable, this is how the user will add new fields
        // to a form
        $('#occams-form-types > ul > li').draggable({
            containment: '#occams-form-editor',
            cursor: 'move',
            helper: 'clone',
            revert: true,
            start: onTypeDragStart,
        });

        // Register handlers for edit/delete fieldsets
        $('.occams-form-fieldset > .occams-form-metadata .occams-form-edit').click(onFieldsetEditStart);
        $('.occams-form-fieldset > .occams-form-metadata .occams-form-delete').click(onFieldsetDeleteStart);
        
        // Register handlers for edit/delete fields
        $('.occams-form-field .occams-form-edit').click(onFieldEditStart);
        $('.occams-form-field .occams-form-delete').click(onFieldDeleteStart);
    }
    
    var onTypeDragStart = function(event, ui) {
        var trigger = $(this);
        console.log(trigger.width());
        $(ui.helper).width( trigger.width() );
    };
    
    var onFieldsetEditStart = function(event) {
        event.preventDefault();
    };
    
    var onFieldsetDeleteStart = function(event) {
        event.preventDefault();
    };
    
    var onFieldEditStart = function(event) {
        event.preventDefault();
        var trigger = $(this);
        var widget = trigger.parents('.occams-form-field').find('.occams-form-widget');
        var url = trigger.attr('href') + ' #form';
        widget.load(url, onFieldEditFormLoad);
    };
    
    var onFieldEditFormLoad = function(){
        var trigger = $(this);
        trigger.find('.formControls input[name*="save"]').click(onFieldEditFormSave);
        trigger.find('.formControls input[name*="cancel"]').click(onFieldEditFormCancel);
    };
    
    var onFieldEditFormSave = function(event) {
        event.preventDefault();
        var trigger = $(this);
        var widget = trigger.parents('.occams-form-field').find('.occams-form-widget');
        var form = $(trigger.attr('form'));
        var url = form.attr('action') + ' #form'
        var data = form.serializeArray()
        data.push({name: 'form.buttons.save', value: 'Apply'});
        widget.load(url, data, onFieldEditFormLoad);
    };
    
    var onFieldEditFormCancel = function(event) {;
        event.preventDefault();
        var trigger = $(this);
        console.log('cancel');
    };
    
    var onFieldDeleteStart = function(event) {
        event.preventDefault();
        $.ajax({
            url: '/Plone/testing/fia-forms-1/LumbarPuncture/test_source/@@test',
            success: function (data){
                console.log(data);
            },
        });
    };
    
    $(document).ready(main);

})(jQuery);
