/**
 * OCCAMS Form Editor Application 
 */
(function($){
    'use strict';
     
    /**
     * Main method that initializes all components
     */
    var main = function() {
        
        // Disable text selection, because it's annoying when dragging/dropping
        $('#occams-form-editor').disableSelection();
        
        // Handle scrolling events to reposition the sidebar
        $(window).scroll(onWindowScroll);
        // We also need to do it for resize because the method uses black magic...
        $(window).resize(onWindowScroll);
        
        // Configure fieldsets as sortable within the editor, note that using
        // 'intersect' as a tolerance won't work here because the forms
        // can get rather huge and so it will look weird.
        $('#occams-form-fieldsets').sortable({
            axis: 'y',
            items: '.occams-form-fieldset:not(:first)',
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
        $('#occams-form-basic-types li').draggable({
            containment: '#occams-form-editor',
            connectToSortable: '.occams-form-fields',
            cursor: 'move',
            helper: 'clone',
            revert: 'invalid',
            start: onTypeDragStart,
            zIndex: 9001,
        });
        
        // TODO: can't do fieldsets for some reason

        // Register handlers for edit/delete fieldsets
        $('.occams-form-fieldset > .occams-form-metadata .occams-form-edit').click(onFieldsetEditStart);
        $('.occams-form-fieldset > .occams-form-metadata .occams-form-delete').click(onFieldsetDeleteStart);
        
        // Register handlers for edit/delete fields
        $('.occams-form-field .occams-form-edit').click(onFieldEditStart);
        $('.occams-form-field .occams-form-delete').click(onFieldDeleteStart);
    };
        
    /**
     * Repositions the side bar on window scroll.
     * 
     * @param   event   The DOM event for the window scroll.
     */
    var onWindowScroll = function(event) {
        var editor = $('#occams-form-editor');
        var mainbar = $('#occams-form-mainbar');
        var sidebar = $('#occams-form-sidebar');
        var editorOffset = editor.offset();
        var scrollY = $(window).scrollTop();
        
        // Reposition if the window if the scrolling position is past the editor
        if (scrollY >= editorOffset.top) {
            var left = editorOffset.left + mainbar.width();
            sidebar.css({position: 'fixed', top: 0, right: '', left: left + 'px'});
        } else {
            sidebar.css({position: 'absolute', top: 0, right: 0, left: ''});
        }
        
    };
    
    var onTypeDragStart = function(event, ui) {
        var trigger = $(this);
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
        var widgetPreview = widget.find('.field');
        widget.append('<div class="inline-editor"></div>')
        var widgetEditor = widget.find('.inline-editor');
        
        // It's really bad form to use the ID because it will be injected into
        // the page multiple times, meaning there will be multiple #form elements.
        // This is the only way I could ge this to work though.
        var url = trigger.attr('href') + ' #form';
        widgetPreview.css({display: 'none'});
        widgetEditor.load(url, onFieldEditFormLoad);
    };
    
    var onFieldEditFormLoad = function(){
        var trigger = $(this);
        trigger.find('.formControls input[name*="apply"]').click(onFieldEditFormSave);
        trigger.find('.formControls input[name*="cancel"]').click(onFieldEditFormCancel);
    };
    
    var onFieldEditFormSave = function(event) {
        event.preventDefault();
        var trigger = $(this);
        var widget = trigger.parents('.occams-form-field').find('.occams-form-widget');
        var form = $(trigger.attr('form'));
        var url = form.attr('action') + ' #form'
        var data = form.serializeArray();
        data.push({name: 'form.buttons.apply', value: 'Apply'});
        widget.load(url, data, onFieldEditFormLoad);
    };
    
    var onFieldEditFormCancel = function(event) {
        event.preventDefault();
        var trigger = $(this);
        var widget = trigger.parents('.occams-form-field').find('.occams-form-widget');
        var widgetPreview = widget.find('.field');
        var widgetEditor = widget.find('.inline-editor');
        
        widgetPreview.css({display: 'block'});
        widgetEditor.remove();
    };
    
    var onFieldDeleteStart = function(event) {
        event.preventDefault();
        var trigger = $(this);
        var editor = trigger.parents('.occams-form-field')
        editor.remove();
//        $.ajax({
//            url: '/Plone/testing/fia-forms-1/LumbarPuncture/test_source/@@test',
//            success: function (data){
//                console.log(data);
//            },
//        });
    };
    
    $(document).ready(main);

})(jQuery);
