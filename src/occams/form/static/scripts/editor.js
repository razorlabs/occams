/**
 * OCCAMS Form Editor Application 
 */

/**
 * Application Setup
 */
(function($){
    'use strict';
     
    /**
     * Main method that initializes all components.
     * Since there are no scoped variables we don't need to worry about
     * closure and so can declare the callback directly as a parameter.
     */    
    $(document).ready(function() {
        // Floating Types Panel
        $('#occams-form-aux').floatingPanel({
            containment: '#occams-form-editor',
        });
        
        // Fieldset Items
        $('#occams-form-fieldsets').formItems({
            containment: '#occams-form-editor',
            editButton: '.occams-form-fieldset > .occams-form-head .occams-form-editable',
            deleteButton: '.occams-form-fieldset > .occams-form-head .occams-form-deleteable',
            itemsFrom: '#occams-form-new li:has(a[class="object"])',
            itemClass: 'occams-form-fieldset',
        });
        
        // Field Items
        $('.occams-form-fields').formItems({
            containment: '#occams-form-editor',
            editButton: '.occams-form-field > .occams-form-head .occams-form-editable',
            deleteButton: '.occams-form-field > .occams-form-head .occams-form-deleteable',
            itemsFrom: '#occams-form-new li:not(:has(a[class="object"]))',
            itemClass: 'occams-form-field',
        });
    });

})(jQuery);


/**
 * Form Items Plug-in
 */
(function($){
    'use strict';
    
    var methods = {
        /**
         * Plug-in initialization
         */
        init: function(options) {            
            options = $.extend({
                containment: null,
                itemClass: null,
                itemsFrom: null,
                editButton: null,
                deleteButton: null,
            }, options);
            
            $(this).sortable({
                axis: 'y',
                connectWith: this.selector,
                cursor: 'move',
                forcePlaceholderSize: false,
                opacity: 0.6,
                receive: methods._onSortableRecieve,
                remove: methods._onSortableRemove,
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
            $(options.itemsFrom).find('a').click(methods._onNewClick);
            
            // Register handlers for edit/delete fields
            $(this).find(options.editButton).click(methods._onEditClick);
            $(this).find(options.deleteButton).click(methods._onDeleteClick);
            
            return this;
        },
        
        _doError: function(msg) {
            alert(msg);
        },
        
        /**
         * DOM handler for when an item from the "new item" list is clicked
         */
        _onNewClick: function(event) {
            event.preventDefault();
        },
        
        /**
         * jQuery handler for when this list receives a new item from another list.
         * 
         * In some cases it will be a new item, in which a request is made to
         * create one.
         */
        _onSortableReceive: function(event, ui) {
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
        _onSortableRemove: function(event, ui) {
            console.log('removed');
        },        
        
    
        /**
         * 
         */
        _onAddFormLoad: function(response, status, xhr) {
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
         * DOM handler when the edit button for an item is clicked
         * 
         * Note: It's really bad form to use the ID because it will be 
         * injected into the page multiple times, meaning there will be multiple 
         * #form elements. This is the only way I could get this to work though.
         */
        _onEditClick: function(event) {
            event.preventDefault();
            var trigger = $(this);
            var url = $.trim(trigger.attr('href')) + ' #form';
            trigger.parents('.occams-form-field').find('.occams-form-edit').load(url, methods._onEditFormLoad);
        },
        
        /**
         * XHR handler for when the edit form finishes loading.
         * Basically sets up the form and begins the fancy animation chain.
         */
        _onEditFormLoad: function(response, status, xhr){
            if (status != 'success') {
                methods._doError('Failed to load edit form');
                return;
            }
                        
            // configure loaded form before displaying
            var trigger = $(this);
            var item = trigger.closest('.occams-form-item');
            item.find('.formControls input[name*="apply"]').click(methods._onEditFormSaveClick);
            item.find('.formControls input[name*="cancel"]').click(methods._onEditFormCancelClick);
            
            // Run datagridfield's setup, since it assumes the DOM was already
            // there, but it's not because we dynamically load it. 
            // Also fix it so that it triggers when the actual input element is
            // changed.
            item.find('.auto-append > .datagridwidget-cell input')
                .change(dataGridField2Functions.autoInsertRow);
            
            // begin form display chain
            item.find('.occams-form-view').slideUp('fast', methods._onViewerDisabled);
        },

        /**
         * When all animations are complete, we're ready to start the editor for
         * an item
         */
        _onViewerDisabled: function() {
            $(this).closest('.occams-form-item').find('.occams-form-edit').slideDown('fast', null);
        },
        
        /**
         * 
         */
        _onEditorDisabled: function() {
            $(this).closest('.occams-form-item').find('.occams-form-view').slideDown('fast', null);
            $(this).closest('.occams-form-item').find('.occams-form-edit').children().remove();
        },
        
        /**
         * DOM handler when the save button is clicked on the edit form. 
         */
        _onEditFormSaveClick: function(event) {
            event.preventDefault();
            var trigger = $(this);            
            var form = $(trigger.attr('form'));
            var viewer = trigger.closest('.occams-form-item').find('.occams-form-view:first');
            var url = form.attr('action') + ' #form'
            var data = form.serializeArray();
            data.push({name: $(this).attr('name'), value: $(this).attr('value')});
            // Disable the submit button so the user doesn't go click-happy
            $(this).attr({disabled: 'disabled', value: 'Saving...'});
            viewer.load(url, data, methods._onEditFormSaveLoad);
        },
        
        /**
         * XHR event when the form data is submitted and a response is returned.
         */
        _onEditFormSaveLoad: function(response, status, xhr) {
            if (status != 'success') {
                methods._doError('Failed to load save form');
                return;
            }
            $(this).closest('.occams-form-item')
                .find('.occams-form-edit')
                .slideUp('fast', methods._onEditorDisabled);
        },
        
        /**
         * DOM handler when the cancel button is clicked on the edit form.
         */
        _onEditFormCancelClick: function(event) {
            event.preventDefault();
            $(this).closest('.occams-form-item')
                .find('.occams-form-edit')
                .slideUp('fast', methods._onEditorDisabled);
        },
        
        /**
         * DOM handler for when the delete button for the item is clicked
         */
        _onDeleteClick: function(event) {
            event.preventDefault();
            var trigger = $(this);
            var url = $.trim(trigger.attr('href')) + ' #form';
            trigger
                .closest('.occams-form-item')
                .find('.occams-form-edit:first')
                .load(url, methods._onDeleteFormLoad);
        },
        
        /**
         * XHR handler for when the delete form is loaded 
         */
        _onDeleteFormLoad: function(response, status, xhr){
            // configure loaded form before displaying
            var trigger = $(this);
            var item = trigger.closest('.occams-form-item');
            item.find('.formControls input[name*="confirm"]').click(methods._onDeleteFormConfirmClick);
            item.find('.formControls input[name*="cancel"]').click(methods._onDeleteFormCancelClick);
            
            // begin form display chain
            item.find('.occams-form-view').slideUp('fast', methods._onViewerDisabled);
        },
        
        /**
         * DOM handler for when the confirm button is clicked for item deletion.s
         */
        _onDeleteFormConfirmClick: function(event){
            event.preventDefault();
            var form = $($(this).attr('form'));
            var url = form.attr('action');
            var data = form.serializeArray();
            data.push({name: $(this).attr('name'), value: $(this).attr('value')});
            $(this).attr({disabled: 'disabled', value: 'You\'re in trouble now...'});
            $.ajax({url: url, complete: methods._onDeleteFormConfirmLoad.bind(this)});
        },
        
        /**
         * XHR handler for when the confirm delete request is completed 
         */
        _onDeleteFormConfirmLoad: function(response, status, xhr) {
            if (status != 'success') {
                methods._doError('Failed to delete item :(');
                return;
            }
            
            $(this).closest('.occams-form-item').fadeOut('fast', methods._onDeleted)
        },
        
        /**
         * When delete animation is complete remove the DOM contents for the 
         * item.
         */
        _onDeleted: function() {
            $(this).remove();
        },
        
        /**
         * DOM handler for when the cancel button is clicked on the delete
         * confirmation form.
         */
        _onDeleteFormCancelClick: function(event){
            event.preventDefault();
            $(this).closest('.occams-form-item')
                .find('.occams-form-edit')
                .slideUp('fast', methods._onEditorDisabled);
        },  
    };
    
    /**
     * Plug-in namespace registration
     */
    $.fn.formItems = function( options ) {
        return methods.init.apply( this, arguments );
    };
    
})(jQuery);

/**
 * Floating Panel Plug-in
 */
(function($){
    'use strict';
    
    var methods = {
        /**
         * Plug-in initialization
         */
        init: function(options) {
            options = $.extend({
                containment: null,
            }, options);
            
            $(this).data('floatingPanel', {
                target: $(this),
                options: options,
            })
            
            // Handle scrolling events to reposition this panel
            $(window).scroll(methods._onWindowScroll.bind(this));
            
            return this;
        },
        
        /**
         * Repositions the panel on window scroll.
         */
        _onWindowScroll: function(event) {
            var data = $(this).data('floatingPanel');
            var container = $(data.options.containment);
            var panel = $(this);
            var containerOffset = container.offset();
            var scrollY = $(window).scrollTop();
            
            // Reposition if the window if the scrolling position is past the editor
            // Note that we only need to re-render if it hasn't been set yet. 
            if (scrollY >= containerOffset.top) {
                if(panel.css('position') != 'fixed') {
                    var right = $(window).width() - (panel.offset().left + panel.width());
                    panel.css({position: 'fixed', top: 0, right: right + 'px'});
                }
            } else {
                if ( panel.css('position') != 'absolute' ) {
                    panel.css({position: 'absolute', top: 0, right: 0});
                }
            }
        },
    };
    
    /**
     * Plug-in namespace registration
     */
    $.fn.floatingPanel = function( options ) {
        return methods.init.apply( this, arguments );
    };
    
})(jQuery);

