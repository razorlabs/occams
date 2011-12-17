/**
 * OCCAMS Form Editor Application 
 */
(function($){
    'use strict';
     
    /**
     * Main method that initializes all components
     */
    var onReady = function() {
        // No need to continue if the editor is not on this page
        if ( ! $('#occams-form-editor').length ){
            return;
        }
                
        // Handle scrolling events to reposition the sidebar
        $(window).scroll(onWindowScroll);
        
        // Configure fieldsets as sortable within the editor, note that using
        // 'intersect' as a tolerance won't work here because the forms
        // can get rather huge and so it will look weird.
        $('#occams-form-fieldsets').sortable({
            axis: 'y',
            cursor: 'move',
            forcePlaceholderSize: false,
            opacity: 0.6,
            receive: onFieldsetSortReceive,
            remove: onFieldsetSortRemove,
        });
        
        // Configure fields as sortable within fieldsets (and across fieldsets)
        $('.occams-form-fields').sortable({
            axis: 'y',
            connectWith: '.occams-form-fields',
            cursor: 'move',
            forcePlaceholderSize: false,
            opacity: 0.6,
            receive: onFieldSortReceive,
            remove: onFieldSortRemove,
            tolerance: 'intersect',
        });
        
        $('#occams-form-new li a').click(onNewFieldClick);
        
        // Configure types as draggable, this is how the user will add new fields
        // to a form. Also, using ``connectToSortable``, we can add it
        // to the fields listing. We handle new fields using the sortable's
        // ``receive`` event because using droppable's ``drop`` causes two
        // events to be triggered, a known jQuery bug.
        $('#occams-form-new li:not(:has(a[class="object"]))').draggable({
            containment: '#occams-form-editor',
            connectToSortable: '.occams-form-fields',
            cursor: 'move',
            // TODO: should be changed to a more suitable div
            helper: 'clone',
            revert: 'invalid',
            zIndex: 9001,
        });
        
        $('#occams-form-new li:has(a[class="object"])').draggable({
            containment: '#occams-form-editor',
            connectToSortable: '#occams-form-fieldsets',
            cursor: 'move',
            // TODO: should be changed to a more suitable div
            helper: 'clone',
            revert: 'invalid',
            zIndex: 9001,
        });
        
        // Register handlers for edit/delete fieldsets
        $('.occams-form-fieldset > .occams-form-metadata .occams-form-edit').click(onFieldsetEditStart);
        $('.occams-form-fieldset > .occams-form-metadata .occams-form-delete').click(onFieldsetDeleteStart);
        
        // Register handlers for edit/delete fields
        $('.occams-form-field .occams-form-editable').click(onFieldEditStart);
        $('.occams-form-field .occams-form-deleteable').click(onFieldDeleteStart);
    };
            
    /**
     * Repositions the side bar on window scroll.
     */
    var onWindowScroll = function(event) {
        var editor = $('#occams-form-editor');
        var aux = $('#occams-form-aux');
        var editorOffset = editor.offset();
        var scrollY = $(window).scrollTop();
        
        // Reposition if the window if the scrolling position is past the editor
        // Note that we only need to re-render if it hasn't been set yet. 
        if (scrollY >= editorOffset.top) {
            if(aux.css('position') != 'fixed') {
                var right = $(window).width() - (aux.offset().left + aux.width());
                aux.css({position: 'fixed', top: 0, right: right + 'px'});
            }
        } else {
            if ( aux.css('position') != 'absolute' ) {
                aux.css({position: 'absolute', top: 0, right: 0});
            }
        }
        
    };

    /**
     * 
     */
    var onNewFieldClick = function(event) {
        event.preventDefault();
    };

    /**
     * 
     */
    var onFieldsetSortReceive = function(event, ui) {
        var trigger = $(this);
        
        if (! $(ui.sender).hasClass('occams-form-fields')) {
            // Unfortunately, jQuery UI has a bug where ``ui.item``isn't 
            // actually the received item. This only occurs when sorting
            // a dropped item (``conntectToSortable``).
            // So instead, we find any newly dropped items....
            if (! trigger.hasClass('ui-draggable')){
                trigger = $(this).find('.ui-draggable');
            }
            
            var url = $.trim(trigger.find('a').attr('href')) + ' #form';
            var newField = $('#occams-form-item-template .occams-form-item').clone().addClass('occams-form-fieldset');
            
            trigger.replaceWith(newField);

            newField.find('.occams-form-view').css({display: 'none'});
            newField.find('.occams-form-edit').css({display: 'block'}).load(url, onFieldsetAddFormLoad);
            
        } else {
            // TODO: handle the moving of another field here.
            console.log('add item to this list');
        }
    };

    /**
     * 
     */
    var onFieldsetSortRemove = function(event, ui) {
        
    };

    /**
     * 
     */
    var onFieldsetAddFormLoad = function(event, ui) {
        
    };

    /**
     * Handles when an field is received from another listing. 
     * In some cases it will be a new field, in which a request is made to
     * create one.
     */
    var onFieldSortReceive = function(event, ui) {
        var trigger = $(this);
        
        if (! $(ui.sender).hasClass('occams-form-fields')) {
            // Unfortunately, jQuery UI has a bug where ``ui.item``isn't 
            // actually the received item. This only occurs when sorting
            // a dropped item (``conntectToSortable``).
            // So instead, we find any newly dropped items....
            if (! trigger.hasClass('ui-draggable')){
                trigger = $(this).find('.ui-draggable');
            }
            
            var url = $.trim(trigger.find('a').attr('href')) + ' #form';
            var newField = $('#occams-form-item-template .occams-form-item').clone().addClass('occams-form-field');
            
            trigger.replaceWith(newField);

            newField.find('.occams-form-view').css({display: 'none'});
            newField.find('.occams-form-edit').css({display: 'block'}).load(url, onFieldAddFormLoad);
            
        } else {
            // TODO: handle the moving of another field here.
            console.log('add item to this list');
        }
    };
    
    var onFieldAddFormLoad = function(response, status, xhr) {
        var trigger = $(this);
        trigger.find('.formControls input[name*="add"]').click(onFieldAddFormSave);
        trigger.find('.formControls input[name*="cancel"]').click(onFieldAddFormCancel);
    };
    
    /**
     * 
     */
    var onFieldAddFormSave = function(event) {
        event.preventDefault();
        var trigger = $(this);
        var widget = trigger.parents('.occams-form-field').find('.occams-form-widget');
        var form = $(trigger.attr('form'));
        var url = form.attr('action') + ' #form'
        var data = form.serializeArray();
        data.push({name: 'form.buttons.apply', value: 'Apply'});
        widget.load(url, data, onFieldEditFormLoad);
    };
    
    /**
     * 
     */
    var onFieldAddFormCancel = function(event) {
        event.preventDefault();
        var trigger = $(this);
        var widget = trigger.parents('.occams-form-field').find('.occams-form-widget');
        var widgetPreview = widget.find('.field');
        var widgetEditor = widget.find('.inline-editor');
        
        widgetPreview.css({display: 'block'});
        widgetEditor.remove();
    };
    
    /**
     * 
     */
    var onFieldSortRemove = function(event, ui) {
        // TODO: handle the moving of the field elsewhere (i.e. removed)
        console.log('moved out');
    };

    /**
     * 
     */
    var onFieldsetEditStart = function(event) {
        event.preventDefault();
    };
    
    /**
     * 
     */
    var onFieldsetDeleteStart = function(event) {
        event.preventDefault();
    };
    
    /**
     * 
     */
    var onFieldEditStart = function(event) {
        event.preventDefault();
        var trigger = $(this);
        
        // It's really bad form to use the ID because it will be injected into
        // the page multiple times, meaning there will be multiple #form elements.
        // This is the only way I could ge this to work though.
        var url = $.trim(trigger.attr('href')) + ' #form';
        trigger.parents('.occams-form-field').find('.occams-form-view').css({display: 'none'});
        trigger.parents('.occams-form-field').find('.occams-form-edit').css({display: 'block'}).load(url, onFieldEditFormLoad);
    };
    
    /**
     * 
     */
    var onFieldEditFormLoad = function(response, status, xhr){
        var trigger = $(this);
        trigger.find('.formControls input[name*="apply"]').click(onFieldEditFormSave);
        trigger.find('.formControls input[name*="cancel"]').click(onFieldEditFormCancel);
    };
    
    /**
     * 
     */
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
    
    /**
     * 
     */
    var onFieldEditFormCancel = function(event) {
        event.preventDefault();
        var trigger = $(this);
        var widget = trigger.parents('.occams-form-field').find('.occams-form-widget');
        var widgetPreview = widget.find('.field');
        var widgetEditor = widget.find('.inline-editor');
        
        widgetPreview.css({display: 'block'});
        widgetEditor.remove();
    };
    
    /**
     * 
     */
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
    
    $(document).ready(onReady);

})(jQuery);
