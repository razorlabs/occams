/**
 * @fileOverview OCCAMS Form Editor Application
 *
 * A note on module setup: methods are broken up into possible editor states,
 * with setup/transitions/ajax contained as nested methods. The reason for
 * this style of implementation is to make the code (hopefully) less confusing
 * to follow.
 */
+function($) {
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
                cancel: '.of-frozen',
                cursor : 'move',
                forcePlaceholderSize : false,
                placeholder : 'of-placeholder',
                handle: '.of-metadata',
                revert: true,
                opacity : 0.9,
            },
        };

    /**
     * Returns the URL of the item based on it's location in the DOM tree
     */
    var getItemUrl = function(item){
        // Make sure we have an item
        item = $(item).closest('.of-item');
        var pathNodes = [];
        var baseUrl = $('base').attr('href') || window.location.href;
        if (item.length) {
            pathNodes.unshift($(item).attr('dataset').name);
            $(item).parents('.of-item').each(function(){
                pathNodes.unshift($(this).attr('dataset').name);
            });
        }

        return  baseUrl.replace(/\/$/, '') + '/' + pathNodes.join('/');
    };

    /**
     * Forces the item to update itself based on it's location in the DOM tree
     * @param item          the DOM element to update
     * @param properties    A mapping containing additional property update values
     *                      Possible values include (all optional):
     *                          - name
     *                          - title
     *                          - description
     *                          - view (html content of the new view)
     */
    var updateItem = function(item, properties) {
        // Make sure we have an item
        item = $(item).closest('.of-item');
        var previewer = item.find('.of-content:first > .of-view');

        if (item.hasClass('of-fieldset') && !previewer.hasClass('of-fields')) {
            // Configure the newly added fieldset
            previewer.addClass('of-fields');
            configureFields();
        }

        item.find('.of-controls:first').removeClass('of-disabled');

        // Set the visible labels
        item.find('.of-name:first').text(properties.name);
        item.find('.of-title:first').text(properties.title);
        item.find('.of-description:first').text(properties.description);

        // Set the new data values
        $(item.attr('dataset')).attr({
            name: properties.name,
            type: properties.type,
        });

        // Update the urls
        var url = getItemUrl(item);
        item.find('.of-editable').attr('href', url + '/@@edit');
        item.find('.of-deleteable').attr('href', url + '/@@delete');

        // Re-render the widget if possible
        if (properties.view) {
            var widgetView = $(properties.view).find('#form .field')
            previewer.empty().append(widgetView);
        }
    };

    /**
     * Updates the status of the closest collapseable button
     */
    var updateCollapseableState = function(node) {
        var fieldset = $(node).closest('.of-fieldset');
        var button = fieldset.find('.of-collapseable');
        if (fieldset.find('form').length > 0) {
            button.addClass('of-disabled');
        } else {
            button.removeClass('of-disabled');
        }
    };

    /**
     * DOM handler when item form data is submitted
     */
    var onItemDataSubmitClick = function(event){
        event.preventDefault();
        var trigger= $(event.target);
        var form = $(trigger.attr('form'));
        var content = form.closest('.of-content');
        var item = content.closest('.of-item');

        $.ajax({
            type: 'POST',
            dataType: 'text',
            url: form.attr('action'),
            data: form.serializeArray().concat([{
                // Add the submit button data as well since it doesn't get added
                name: trigger.attr('name'),
                value: trigger.attr('value')
                }]),
            success: function(response, status, xhr) {
                // Remove errors, if any
                content.removeClass('of-error');

                // Handle data based on action
                switch(trigger.attr('name')){
                    case 'add.buttons.add':
                    case 'edit.buttons.apply':
                        var editor = item.find('.of-content:first > .of-edit');
                        var previewer = item.find('.of-content:first > .of-view');
                        var properties = null;

                        try{
                            properties = $.parseJSON(response);
                        } catch(error) {
                            // The page was returned back, render it
                            editor.empty().append($(response).find('#content form'));
                        }

                        // Update the item with it's new properties
                        if (properties) {
                            updateItem(item, properties);
                            editor.slideUp('fast', function(){
                                editor.empty();
                                previewer.slideDown('fast');
                                item.removeClass('of-frozen');
                                updateCollapseableState(item);
                            });
                        }

                        break;

                    case 'delete.buttons.delete':
                        item.fadeOut('fast', function(){
                            item.remove();
                        });
                        break;
                }
            },
        });
    };

    /**
     * DOM handler when item editing is canceled
     */
    var onItemDataCancelClick = function(event){
        event.preventDefault();
        var trigger = $(event.target);
        var item = $(event.target).closest('.of-item');

        if ( $(event.target).attr('name') == 'add.buttons.cancel' ) {
            // Handle add cancel differently by removing the entire element tree
            item.fadeOut('fast', function(){
                item.remove();
            });
        } else {
            var content = trigger.closest('.of-content');
            var editor = content.find('.of-edit:first');
            var viewer = content.find('.of-view:first');
            editor.slideUp('fast', function(){
                content.removeClass('of-error');
                editor.empty();
                viewer.slideDown('fast', function(){
                    // Enable buttons once animation is complete
                    item.find('.of-controls:first').removeClass('of-disabled');
                    item.removeClass('of-frozen');
                    updateCollapseableState(item);
                });
            });
        }
    };

    /**
     * jQuery UI handler for when a draggable is dropped into the fields list
     */
    var onDraggableReceived = function(event, ui) {
        if (!$(ui.item).hasClass('of-item')) {
            var target = $(event.target);
            // jQuery doesn't give the correct ``ui.item`` for draggable items
            var draggable = $(target).find('.ui-draggable').first();
            var previous = draggable.prevAll('[data-name!=""]:first');
            var type = $(draggable).attr('dataset').type;
            var url = getItemUrl(draggable) + '/@@add-' + type + ' #content form';
            var data = {after: $(previous.attr('dataset')).attr('name') || ''};
            var newItem =
                $('#of-item-template .of-item')
                .clone()
                .addClass(type == 'object' ? 'of-fieldset' : 'of-field')
                .addClass('of-' + type)
                .addClass('of-frozen')
                ;

            // Configure the new item
            newItem.find('.of-type:first').text(type);
            newItem.find('.of-name:first').text('[...]');
            newItem.find('.of-content:first > .of-view').css({display: 'none'});
            newItem.find('.of-controls:first').addClass('of-disabled');

            // Load the editor into the new item
            $(draggable).replaceWith(newItem);

            newItem
                .find('.of-content:first > .of-edit')
                .load(url , data, function(){
                    updateCollapseableState(newItem);
                    newItem.find('.of-content:first > .of-edit').slideDown('fast');
                });
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
                url = getItemUrl(ui.sender) +'/'+ $(ui.item).attr('dataset').name;
            } else {
                url = getItemUrl(ui.item);
            }

            // Find the previous element that is not currently being added
            var previous = $(ui.item).prevAll('[data-name!=""]:first');

            $.ajax({
                type: 'POST',
                url: url + '/@@order',
                data: {
                    'form.widgets.target':
                        $(event.target).closest('.of-item').attr('dataset').name,
                    'form.widgets.after':
                        $(previous.attr('dataset')).attr('name') || '',
                    'form.buttons.apply': 1,
                    },
                error: function(xhr, status, thrown){
                    $(ui.sender || event.target).sortable('cancel');
                },
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
        var trigger = $(event.target);
        var item = trigger.closest('.of-item');
        if (item.find('form').length <= 0){
            $(event.target)
                .toggleClass('of-collapsed')
                .closest('.of-item')
                .find('.of-content:first')
                .slideToggle('fast');
        }
    };

    /**
     * DOM Event handler when an item's action button is clicked
     */
    var onActionClick = function(event) {
        event.preventDefault();
        var trigger = $(event.target);
        // Only take an action if the item's action buttons are not disabled
        if (!$(trigger).closest('.of-controls').hasClass('of-disabled')){
            var url = $(trigger).attr('href');
            var selector = '#content form';
            $(trigger).closest('.of-controls').addClass('of-disabled');
            $(trigger)
                .closest('.of-item').addClass('of-frozen')
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

                    updateCollapseableState(editor);
                    previewer.slideUp('fast', function(){
                        editor.slideDown('fast');
                    });
                });
        }
    };

    /**
     * DOM handler when the form editor is committed
     */
    var onEditorSubmitClick = function(event){
        // Find any nested form elements
        var trigger = $(event.target);
        var unstaged = trigger.closest('form').find('form');

        if ( unstaged.length > 0 ) {
            event.preventDefault();

            // The position of the first error
            var targetY = unstaged.first().closest('.of-item').offset().top;

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
            .delegate('a.of-editable', 'click', onActionClick)
            .delegate('a.of-deleteable', 'click', onActionClick)
            .delegate('a.of-collapseable', 'click', onCollapseableClick)
            .delegate('input[name="add.buttons.add"]', 'click', onItemDataSubmitClick)
            .delegate('input[name="add.buttons.cancel"]', 'click', onItemDataCancelClick)
            .delegate('input[name="edit.buttons.apply"]', 'click', onItemDataSubmitClick)
            .delegate('input[name="edit.buttons.cancel"]', 'click', onItemDataCancelClick)
            .delegate('input[name="delete.buttons.delete"]', 'click', onItemDataSubmitClick)
            .delegate('input[name="delete.buttons.cancel"]', 'click', onItemDataCancelClick)
            ;

        // Make sure there are no active edits before committing changes
        $('#form #form-buttons-submit').click(onEditorSubmitClick);

        // Prevent click-happy users from resending the form
        $('#content').delegate('form', 'submit', function(event){
            // At this point, all validation should have occurred at the click
            // level, so there is no need to enable/re-enable buttons
            var trigger = $(event.target);
            // Don't submit if already submitting
           if (trigger.data('of-submitted')){
                event.preventDefault();
            } else {
                trigger.data('of-submitted', true);
                trigger.find(':submit').addClass('of-disabled');
            }
        });
    };

    /**
     * Configures datagridfield's actions since we load it via ajax
     */
    var configureDatagridField = function(){
        $('#of-editor')
            .delegate(
                '.auto-append > .datagridwidget-cell input',
                'change',
                function(event){
                    // The function might not be defined yet, so look for it
                    // when actually triggered
                    dataGridField2Functions.autoInsertRow.call(this, event);
                });
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
            configureDatagridField();
            configureActions();
        }
    });

}(jQuery);
