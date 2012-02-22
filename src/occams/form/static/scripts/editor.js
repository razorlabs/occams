/**
 * @fileOverview OCCAMS Form Editor Application
 */
(function($) {
    'use strict';

    /**
     * Common values for UI components
     */
    var settings = {
            draggable: {
                cursor : 'move',
                helper : 'clone',
                revert : 'invalid',
                zIndex : 9001,
            },
            sortable: {
                axis : 'y',
                cursor : 'move',
                forcePlaceholderSize : false,
                placeholder : 'of-placeholder',
                handle: '.of-metadata',
                revert: true,
                opacity : 0.7,
            },
        };

    /**
     * Returns the URL of the item based on it's location in the DOM tree
     */
    var getItemUrl = function(item){
        // Make sure we have an item
        item = $(item).closest('.of-item');

        var baseUrl = $('base').attr('href') || window.location.href;
        var pathNodes = [$(item).attr('dataset').name];

        if (baseUrl[baseUrl.length] != '/'){
            baseUrl += '/';
        }

        $(item).parents('.of-item').each(function(){
            var name = $(this).attr('dataset').name;
            if (name) {
                pathNodes.unshift(name);
            }
        });

        return  baseUrl + pathNodes.join('/');
    };

    /**
     * Refreshes the the item with new incoming data
     * @param item  the DOM element to update
     * @param data  an object containing data
     */
    var refreshItem = function(item, data) {
        // Make sure we have an item
        item = $(item).closest('.of-item');
        var previewer = $(item).find('.of-content:first > .of-view');
        var editor = $(item).find('.of-content:first > .of-edit');

        try{
            data = $.parseJSON(data);
        } catch(error) {
            // The fact that the incoming response could not be parsed
            // indicates that there was an error with the form and so
            // it needs to be re-rendered
            editor.empty().append( $(data).find('#content form') );
            return;
        }

        if ($(item).hasClass('of-fieldset')) {
            previewer.addClass('of-fields');
            // Configure as sortable
            configureFields();
        }

        $(item).find('.of-controls:first').removeClass('of-disabled');

        // Set the visible labels
        $(item).find('.of-name:first').text(data.name);
        $(item).find('.of-title:first').text(data.title);
        $(item).find('.of-version:first').text(data.version);
        $(item).find('.of-description:first').text(data.description);

        // Set the new data values
        $(item).attr('dataset').name = data.name;
        $(item).attr('dataset').type = data.type;
        $(item).attr('dataset').version = data.version;

        // Update the urls
        var url = getItemUrl(item);
        $(item).find('.of-editable').attr('href', url + '/@@edit');
        $(item).find('.of-deleteable').attr('href', url + '/@@delete');

        if (data.view) {
            previewer.empty().append($(data.view).find('#form .field'));
        }

        editor.slideUp('fast', function(){
            editor.empty();
            previewer.slideDown('fast');
        });
    };

    /**
     * DOM handler when item form data is submitted
     */
    var onItemDataSubmitClick = function(event){
        event.preventDefault();
        var trigger= $(event.target);
        var form = $(trigger.attr('form'));
        var url = form.attr('action');
        var data = form.serializeArray().concat([{
            name: $(trigger).attr('name'),
            value: $(trigger).attr('value')
            }]);

        $.post(url, data, function(response, status, xhr){
            var item = $(trigger).closest('.of-item');
            switch($(trigger).attr('name')){
                case 'add.buttons.add':
                case 'edit.buttons.apply':
                    // update the item properties
                    refreshItem(item, response);
                    break;
                case 'delete.buttons.delete':
                    // Elegantly remove the item from the DOM tree
                    $(item).fadeOut('fast', function(){$(this).remove();});
                    break;
            }
        });
    };

    /**
     * DOM handler for the special case of canceling an item add form
     */
    var onAddFormCancelClick = function(event){
        event.preventDefault();
        // Remove the entire item element tree
        $(event.target).closest('.of-item').fadeOut('fast', function(){
            $(this).remove();
        });
    };

    /**
     * DOM handler when item edit is canceled
     */
    var onItemDataCancelClick = function(event){
        event.preventDefault();
        (event.target).closest('.of-edit').slideUp('fast', function(){
            var item = $(this).closest('.of-item');
            item.find('.of-content:first').removeClass('of-error');
            item.find('.of-content:first > .of-edit').empty();
            item.find('.of-content:first > .of-view').slideDown('fast', function(){
                // Enable buttons once animation is complete
                item.find('.of-controls:first').removeClass('of-disabled');
            });
        });
    };

    /**
     * jQuery UI handler for when a draggable is dropped into the fields list
     */
    var onDraggableReceived = function(event, ui) {
        if (!$(ui.item).hasClass('of-item')) {
            var target = $(event.target);
            // jQuery doesn't give the correct ``ui.item`` for draggable items
            var draggable = $(target).find('.ui-draggable').first();
            var type = $(draggable).attr('dataset').type;
            var newItem =
                $('#of-item-template .of-item')
                .clone()
                .addClass(type == 'object' ? 'of-fieldset' : 'of-field')
                .addClass(type)
                ;
            var url = getItemUrl(target) + '/@@add-' + type;
            var selector = '#content form';
            var data = {order: draggable.index()};

            newItem.find('.of-type:first').text(type);
            newItem.find('.of-name:first').text('[...]');
            newItem.find('.of-content:first > .of-view').css({display: 'none'});
            newItem.find('.of-controls:first').addClass('of-disabled');
            newItem
                .find('.of-content:first > .of-edit')
                .load(url + ' ' + selector, data, function(){
                    newItem.find('.of-content:first > .of-edit').slideDown('fast');
                });

            $(draggable).replaceWith(newItem);
        }
    };

    /**
     * jQuery UI handler for when an item from this list is moved.
     */
    var onItemMoved = function(event, ui) {
        if (event.target === ui.item.parent()[0]) {
            var url = null;

            if (ui.sender) {
                // Need to get it's original location for the view to work
                url = getItemUrl(ui.sender) + $(ui.item).attr('dataset').name;
            } else {
                url = getItemUrl(ui.item);
            }

            // Need to use ajax method so we can use the error handler
            $.ajax({
                type: 'POST',
                url: url + '/@@order',
                data: {
                    'form.widgets.target':
                        $(event.target).closest('.of-item').attr('dataset').name,
                    'form.widgets.order': $(ui.item).index(),
                    'form.buttons.apply': 1,
                    },
                error: function(xhr, status, thrown){
                    $(ui.sender || event.target).sortable('cancel');
                }
            });
        }
    };

    /**
     * DOM Event handler when the editor window is scrolled
     */
    var onWindowScroll = function(event){
        var panel = $('#of-aux');

        // Reposition the panel if the scrolling position is past the editor.
        // Note that we only need to re-render if it hasn't been set yet.
        if ( $(window).scrollTop() >= $('#of-editor').offset().top ) {
            if (panel.css('position') != 'fixed') {
                var panelEndX = panel.offset().left + panel.width();
                var windowEndX = $(window).width();
                var right = windowEndX - panelEndX;
                panel.css({position : 'fixed', right : right + 'px'});
            }
        } else {
            if (panel.css('position') != 'absolute') {
                panel.css({ position : 'absolute', right : 0});
            }
        }
    };

    /**
     * DOM Event handler when an item's collapseable button is clicked
     */
    var onCollapseableClick = function(event) {
        event.preventDefault();
        $(event.target)
            .toggleClass('of-collapsed')
            .closest('.of-item')
            .find('.of-content:first')
            .slideToggle('fast');
    };

    /**
     * DOM Event handler when an item's action button is clicked
     */
    var onActionClick = function(event) {
        event.preventDefault();
        var trigger = $(event.target);
        if (!$(trigger).closest('.of-controls').hasClass('of-disabled')){
            var url = $(trigger).attr('href');
            var selector = '#content form';
            $(trigger)
                .closest('.of-item')
                .find('.of-edit:first')
                .load(url + ' ' + selector, function(data, status, xhr) {
                    var content = $(this).closest('.of-content');
                    var editor = content.find('.of-edit:first');
                    var previewer = content.find('.of-view:first');

                    if (content.css('display') == 'none'){
                        editor.css({display: 'none'});
                        previewer.css({display: 'none'});
                        content.css({display: ''});
                    }

                    previewer.slideUp('fast', function(){
                        editor.slideDown('fast');
                    });
                });
        }
    };

    /**
     * DOM handler when the form editor is committed
     */
    var onEditorSubmit = function(event){
        // Find any nested form elements
        var unstaged = $(event.target).closest('form').find('form');

        if ( unstaged.length > 0 ) {
            event.preventDefault();
            // The position of the first error
            var targetY = $(window).height() - unstaged.first().offset().top;

            // Highlight all errors
            unstaged.closest('.of-content').addClass('of-error');

            // Focus on the first error
            $('html, body').animate({scrollTop: targetY}, {duration: 1000});
        }
    };

    /**
     * Configures the side (auxilary) bar content
     */
    var configureAuxilaryBar = function(){
        // Follow the user's scrolling
        $(window).scroll(onWindowScroll);

        // Disable type links so we don't navigate to them
        $('#of-new li a').click(function(event){event.preventDefault();});

        // New fieldset draggables
        $('#of-new li a[class*="object"]')
            .draggable($.extend(settings.draggable, {
                connectToSortable : '#of-fieldsets'
                }));

        // New field draggables
        $('#of-new li a:not([class*="object"])')
            .draggable($.extend(settings.draggable, {
                connectToSortable : '.of-fields'
                }));
    };

    /**
     * Registers the possible actions buttons for the items
     */
    var configureActions = function(){
        // Use delegates to apply to ajax loaded items
        $('#of-editor')
            // Item ations
            .delegate('a.of-editable', 'click', onActionClick)
            .delegate('a.of-deleteable', 'click', onActionClick)
            .delegate('a.of-collapseable', 'click', onCollapseableClick)
            .delegate('input[name="add.buttons.add"]', 'click', onItemDataSubmitClick)
            .delegate('input[name="add.buttons.cancel"]', 'click', onAddFormCancelClick)
            .delegate('input[name="edit.buttons.apply"]', 'click', onItemDataSubmitClick)
            .delegate('input[name="edit.buttons.cancel"]', 'click', onItemDataCancelClick)
            .delegate('input[name="delete.buttons.delete"]', 'click', onItemDataSubmitClick)
            .delegate('input[name="delete.buttons.cancel"]', 'click', onItemDataCancelClick)
            ;

        // Make sure there are no active edits before committing changes
        $('#form #form-buttons-submit').click(onEditorSubmit);
    };

    /**
     * Configures fieldsets as sortables
     */
    var configureFieldsets = function(){
        $('#of-fieldsets').sortable($.extend(settings.sortable, {
            items : '.of-fieldset',
            receive : onDraggableReceived,
            update : onItemMoved,
        }));
    };

    /**
     * Configures fields as sortables
     */
    var configureFields = function(){
        $('.of-fields').sortable($.extend(settings.sortable, {
            connectWith : '.of-fields',
            items : '.of-field',
            receive : onDraggableReceived,
            update : onItemMoved,
        }));
    };

    /**
     * Application initialization
     */
    $(document).ready(function(){
        if ($('#of-editor').length){
            configureFieldsets();
            configureFields();
            configureAuxilaryBar();
            configureActions();
        }
    });

})(jQuery);
