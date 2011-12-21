/**
 * OCCAMS Form Editor Application 
 */


/**
 * Custom Application Plug-ins
 */
(function($){
    'use strict';
    
    var methods = {
        init: function(options) {            
            options = $.extend({
                containment: false,
                itemClass: null,
                itemsFrom: null,
            }, options);
            
            $(this).sortable({
                axis: 'y',
                connectWith: this.selector,
                cursor: 'move',
                forcePlaceholderSize: false,
                opacity: 0.6,
                receive: methods._onSortRecieve,
                remove: methods._onSortRemove,
            });
            
            // Configure types as draggable, this is how the user will add new fields
            // to a form. Also, using ``connectToSortable``, we can add it
            // to the fields listing. We handle new fields using the sortable's
            // ``receive`` event because using droppable's ``drop`` causes two
            // events to be triggered, a known jQuery bug.
            $(options.itemsFrom).draggable({
                containment: options.containment,
                connectToSortable: this.selector,
                cursor: 'move',
                helper: 'clone',
                revert: 'invalid',
                zIndex: 9001,
            });
            
            // Disable type links, to avoid accidental navigation
            $(options.itemsFrom).find('a').click(methods._onNewItemClick);
            
            // Register handlers for edit/delete fieldsets
            $('.occams-form-fieldset > .occams-form-metadata .occams-form-edit').click(onFieldsetEditStart);
            $('.occams-form-fieldset > .occams-form-metadata .occams-form-delete').click(onFieldsetDeleteStart);
            
            // Register handlers for edit/delete fields
            $('.occams-form-field .occams-form-editable').click(onFieldEditStart);
            $('.occams-form-field .occams-form-deleteable').click(onFieldDeleteStart);
            
            return this;
        },
        
        /**
         * DOM handler for when an item from the "new item" list is clicked
         */
        _onNewItemClick: function(event) {
            event.preventDefault();
        },
        
        /**
         * jQuery handler for when this list receives a new item from another list.
         * 
         * In some cases it will be a new item, in which a request is made to
         * create one.
         */
        _onSortReceive: function(event, ui) {
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
                newField.find('.occams-form-edit').css({display: 'block'}).load(url, methods._onAddFormLoad);
                
            } else {
                // TODO: handle the moving of another field here.
                console.log('add item to this list');
            }
        },
        
        /**
         * jQuery handler for when an item from this list is moved elsewhere.
         */
        _onSortRemove: function(event, ui) {
            console.log('removed');
        },        
        
    
        /**
         * 
         */
        _onAddFormLoad = function(response, status, xhr) {
            var trigger = $(this);
            trigger.find('.formControls input[name*="add"]').click(onFieldAddFormSave);
            trigger.find('.formControls input[name*="cancel"]').click(onFieldAddFormCancel);
        },
        
        /**
         * 
         */
        _onFieldAddFormSave: function(event) {
            event.preventDefault();
            var trigger = $(this);
            var widget = trigger.parents('.occams-form-field').find('.occams-form-widget');
            var form = $(trigger.attr('form'));
            var url = form.attr('action') + ' #form'
            var data = form.serializeArray();
            data.push({name: 'form.buttons.apply', value: 'Apply'});
            widget.load(url, data, onFieldEditFormLoad);
        },
        
        /**
         * 
         */
        _onFieldAddFormCancel: function(event) {
            event.preventDefault();
            var trigger = $(this);
            var widget = trigger.parents('.occams-form-field').find('.occams-form-widget');
            var widgetPreview = widget.find('.field');
            var widgetEditor = widget.find('.inline-editor');
            
            widgetPreview.css({display: 'block'});
            widgetEditor.remove();
        },
        
        /**
         * 
         */
        _onFieldsetEditStart: function(event) {
            event.preventDefault();
        };
        
        /**
         * 
         */
        _onFieldsetDeleteStart: function(event) {
            event.preventDefault();
        },
        
        /**
         * 
         */
        onFieldEditStart: function(event) {
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
        _onFieldEditFormLoad: function(response, status, xhr){
            var trigger = $(this);
            trigger.find('.formControls input[name*="apply"]').click(onFieldEditFormSave);
            trigger.find('.formControls input[name*="cancel"]').click(onFieldEditFormCancel);
        },
        
        /**
         * 
         */
        _onFieldEditFormSave: function(event) {
            event.preventDefault();
            var trigger = $(this);
            var field = trigger.parents('.occams-form-field');
            var fieldEditor = field.find('.occams-form-edit');
            var fieldViewer = field.find('.occams-form-view');
            
            var fieldForm = $(trigger.attr('form'));
            var url = fieldForm.attr('action') + ' #form'
            
            var data = fieldForm.serializeArray();
            data.push({name: 'form.buttons.apply', value: 'Apply'});
            fieldViewer.load(url, data, onFieldEditFormLoad);
            
            fieldEditor.css({display: 'none'});
            fieldEditor.children().remove();
            fieldViewer.css({display: 'block'});
        },
        
        /**
         * 
         */
        _onFieldEditFormCancel: function(event) {
            event.preventDefault();
            var trigger = $(this);
            var field = trigger.parents('.occams-form-field');
            var fieldEditor = field.find('.occams-form-edit');
            var fieldViewer = field.find('.occams-form-view');
            
            fieldEditor.css({display: 'none'});
            fieldEditor.children().remove();
            fieldViewer.css({display: 'block'});
        },
        
        /**
         * 
         */
        _onFieldDeleteStart: function(event) {
            event.preventDefault();
            var trigger = $(this);
            var editor = trigger.parents('.occams-form-field')
            editor.remove();
//            $.ajax({
//                url: '/Plone/testing/fia-forms-1/LumbarPuncture/test_source/@@test',
//                success: function (data){
//                    console.log(data);
//                },
//            });
        },
        
        
    };
    
    /**
     * Plug-in namespace registration
     */
    $.fn.formItems = function( method ) {
        // A valid method was specified, call it.
        if ( methods[method] ) {
            var methodArguements = Array.prototype.slice.call( arguments, 1 )
            return methods[method].apply( this, methodArguements);
          
        // No options or method was specified, initialize
        } else if ( typeof method === 'object' || ! method ) {
            return methods.init.apply( this, arguments );
          
        // The method specified is not defined
        } else {
            $.error('Method ' +  method + ' does not exist on jQuery.formItem');
        }    
    };
    
})(jQuery);


/**
 * Application Settings
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
        
        // Fieldset Items
        $('#occams-form-fieldsets').formItems({
            containment: '#occams-form-editor',
            itemsFrom: '#occams-form-new li:has(a[class="object"])',
        });
        
        // Field Items
        $('.occams-form-fields').formItems({
            containment: '#occams-form-editor',
            itemsFrom: '#occams-form-new li:not(:has(a[class="object"]))',
        });
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


    $(document).ready(onReady);

})(jQuery);
