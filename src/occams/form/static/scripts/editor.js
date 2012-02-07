/**
 * @fileOverview OCCAMS Form Editor Application
 *
 * This module was hastely written and should be really be redone.
 *
 */

/**
 * @class jQuery Form Editor Application Plug-in
 */
(function($) {
    'use strict';

    /**
     * jQuery plug-in registration for for items. Unless otherwise specified,
     * ``this`` always refers to the individual item.
     */
    $(document).ready(function() {
        if (!$('#of-editor').length){
            return;
        }

        // TODO this will not work for brand new forms and needs to somehow
        // be redone

        // Fieldset Items
        $('.of-fieldset').formItem({
            containment : '#of-editor',
            sortable : '#of-fieldsets',
            type: 'of-fieldset',
            contains: 'of-fields',
            draggable : '#of-new li a[class*="object"]',
            placeholder : 'of-placeholder',
        });

        // Field Items
        $('.of-field').formItem({
            containment : '#of-editor',
            sortable : '.of-fields',
            type: 'of-field',
            contains: null,
            draggable : '#of-new li a:not([class*="object"])',
            placeholder : 'of-placeholder',
        });

        // Disable type links so we don't navigate to them
        $('#of-new li a').click(function(event) { event.preventDefault(); });

        // Setup the types element as a floating panel (because the
        // forms can -- and will -- get pretty long)
        $(window).scroll(function(event) {
            var panel = $('#of-aux');
            var container = $('#of-editor');
            var containerOffset = container.offset();
            var scrollY = $(window).scrollTop();

            // Reposition the panel if the scrolling position is past the editor
            // Note that we only need to re-render if it hasn't been set yet.
            if (scrollY >= containerOffset.top) {
                if (panel.css('position') != 'fixed') {
                    var panelEndX = panel.offset().left + panel.width();
                    var windowEndX = $(window).width();
                    var right = windowEndX - panelEndX;
                    panel.css({ position : 'fixed', right : right + 'px'});
                }
            } else {
                if (panel.css('position') != 'absolute') {
                    panel.css({ position : 'absolute', right : 0});
                }
            }
        });
    });

})(jQuery);

/**
 * @class jQuery Form Item Plug-in
 */
(function($) {
    'use strict';

    var methods = {
        /**
         * Initializes the item collection (i.e. the plug-in)
         *
         * @construct
         * @private
         */
        _initialize : function(options) {
            return $(this).each(function() {
                var settings = $.extend({
                    containment : null,
                    draggable : null,
                    sortable : null,
                    type: null,
                    contains: null,
                    placeholder : null,
                }, options);

                // Only setup if the item hasn't been initialized with data
                $(this).data('formItem', settings);

                var head = $(this).children('.of-head');
                var controls = head.find('.of-controls');
                var collapseButton = head.find('.of-collapseable');
                var editButton = controls.find('a.of-editable');
                var deleteButton = controls.find('a.of-deleteable');

                editButton.click(methods._onEditClick.bind(this));
                deleteButton.click(methods._onDeleteClick.bind(this));
                collapseButton.click(methods._onCollapseClick.bind(this));

                // Setup the item's parent listing as a sortable
                $(settings.sortable).sortable({
                    axis : 'y',
                    containment : settings.containment,
                    connectWith : settings.sortable,
                    cursor : 'move',
                    forcePlaceholderSize : false,
                    placeholder : settings.placeholder,
                    handle: '.of-metadata',
                    items : '.' + settings.type,
                    revert: true,
                    opacity : 0.6,
                    receive : methods._onReceived,
                    update : methods._onMoved,
                });

                // Configure types as draggable, this is how the user will add
                // new fields to a form. Also, using ``connectToSortable``, we
                // can add it to the fields listing. We handle new fields using
                // the sortable's ``receive`` event because using droppable's
                // ``drop`` triggers duplicate events, a known jQuery bug.
                $(settings.draggable)
                    .data('formItem', settings)
                    .draggable({
                        containment : settings.containment,
                        connectToSortable : settings.sortable,
                        cursor : 'move',
                        helper : 'clone',
                        revert : 'invalid',
                        zIndex : 9001,
                    });
            });
        },

       /**
        *
        * @returns {String}
        */
       url: function(){
           var baseUrl = $('base').attr('href') || window.location.href;
           var pathNodes = [$(this).attr('dataset').name];

           $(this).parents('.of-item').each(function(){
               var name = $(this).attr('dataset').name;
               if (name) {
                   pathNodes.unshift(name);
               }
           });

           if (baseUrl[baseUrl.length] != '/'){
               baseUrl += '/';
           }

           return  baseUrl + pathNodes.join('/');
       },

        /**
         * Refreshes the the item with new incoming data
         * @param data  json data to refresh the item with
         */
        _refresh : function(data) {
            var settings = $(this).data('formItem');
            var view = $(this).find('.of-content:first > .of-view');
            var edit = $(this).find('.of-content:first > .of-edit');

            try{
                data = $.parseJSON(data);
            } catch(error) {
                // The fact that the incoming response could not be parsed
                // indicates that there was an error with the form and so
                // it needs to be re-rendered
                edit.empty().append( $(data).find('#form') );
                return;
            }


            // Set the visible labels
            $(this).find('.of-name').first().text(data.name);
            $(this).find('.of-title').first().text(data.title);
            $(this).find('.of-version').first().text(data.version);
            $(this).find('.of-description').first().text(data.description);

            // Also set the new data values
            $(this).attr('dataset').name = data.name;
            $(this).attr('dataset').type = data.type;
            $(this).attr('dataset').version = data.version;

            // Update the urls
            var url = methods.url.call(this);
            $(this).find('.of-editable').attr('href', url + '/@@edit');
            $(this).find('.of-deleteable').attr('href', url + '/@@delete');

            if (data.view) {
                view.empty().append( $(data.view).find('#form') );
            }

            if (settings.contains){
                view.addClass(settings.contains);
            }

            edit.slideUp('fast', methods._onEditorDisabled.bind(this));
            return this;
        },

        /**
         *
         */
        _enableEditor : function(url, data, next) {
            var selector = $.trim(url) + ' #form';
            $(this).find('.of-content:first > .of-edit').load(selector, data, next);
            $(this).find('.of-controls:first').css({display: 'none'});
            return this;
        },

        /**
         * When all animations are complete, we're ready to start the editor for
         * an item
         */
        _onViewerDisabled : function() {
            $(this).find('.of-content:first > .of-edit').slideDown('fast');
            return this;
        },

        /**
         *
         */
        _onEditorDisabled : function() {
            $(this).find('.of-content:first > .of-edit').children().remove();
            $(this).find('.of-content:first > .of-view').slideDown('fast');
            $(this).find('.of-controls:first').css({display: ''});
            return this;
        },

        /**
         *
         */
        _onDisabled : function() {
            return $(this).remove();
        },

        /**
         * Helper method to setup a form loaded via AJAX
         *
         * @param actions
         *            a map of button names to handler methods
         * @returns ``this``
         */
        _formSetupHelper : function(actions) {

            $(this).find('.formControls input').each(function() {
                var button = $(this);
                var buttonName = button.attr('name');
                var actionName =
                        buttonName.substring(buttonName.lastIndexOf('.') + 1);
                button.bind('click', actions[actionName]);
            });

            // begin form display chain
            $(this).find('.of-content:first > .of-view').slideUp('fast',
                    methods._onViewerDisabled.bind(this));

            return this;
        },

        /**
         *
         */
        _formSubmitHelper : function(event, callback) {
            event.preventDefault();
            var form = $($(event.target).attr('form'));
            var url = form.attr('action');
            var data = form.serializeArray();
            data.push({
                name : $(event.target).attr('name'),
                value : $(event.target).attr('value')
            });
            $.post(url, data, callback);
            return this;
        },

        /**
         *
         * @param event
         * @returns {___anonymous155_14701}
         */
        _onCollapseClick : function(event) {
            event.preventDefault();
            $(this).find('.of-content:first').slideToggle('fast');
            $(event.target).toggleClass('of-collapsed');
            return this;
        },

        /**
         *
         */
        _onEditClick : function(event) {
            event.preventDefault();
            var url = $(event.target).attr('href');
            var callback = methods._onEditFormLoad.bind(this);
            return methods._enableEditor.call(this, url, null, callback);
        },

        /**
         *
         */
        _onDeleteClick : function(event) {
            event.preventDefault();
            var url = $(event.target).attr('href');
            var callback = methods._onDeleteFormLoad.bind(this);
            return methods._enableEditor.call(this, url, null, callback);
        },

        /**
         * XHR handler for when the edit form finishes loading. Basically sets
         * up the form and begins the fancy animation chain.
         */
        _onAddFormLoad : function(response, status, xhr) {
            if (status != 'success') {
                alert('An error has occured while trying to load the add form');
            } else {
                methods._formSetupHelper.call(this, {
                    'add' : methods._onAddFormSubmitClick.bind(this),
                    'cancel' : methods._onAddFormCancelClick.bind(this),
                });
            }
            return this;
        },

        /**
         * XHR handler for when the edit form finishes loading. Basically sets
         * up the form and begins the fancy animation chain.
         */
        _onEditFormLoad : function(response, status, xhr) {
            if (status != 'success') {
                alert('An error occured while trying to load the edit form');
            } else {
                methods._formSetupHelper.call(this, {
                    'apply' : methods._onEditFormSubmitClick.bind(this),
                    'cancel' : methods._onEditFormCancelClick.bind(this),
                });
            }
            return this;
        },

        /**
         * XHR handler for when the edit form finishes loading. Basically sets
         * up the form and begins the fancy animation chain.
         */
        _onDeleteFormLoad : function(response, status, xhr) {
            if (status != 'success') {
                alert('An error occured while trying to load the delete form');
            } else {
                methods._formSetupHelper.call(this, {
                    'delete': methods._onDeleteFormSubmitClick.bind(this),
                    'cancel': methods._onDeleteFormCancelClick.bind(this),
                });
            }
            return this;
        },

        /**
         * DOM handler when the save button is clicked on the edit form.
         */
        _onAddFormSubmitClick : function(event) {
            var callback = methods._onAddFormSubmitComplete.bind(this);
            return methods._formSubmitHelper.call(this, event, callback);
        },

        /**
         * DOM handler when the save button is clicked on the edit form.
         */
        _onEditFormSubmitClick : function(event) {
            var callback = methods._onEditFormSubmitComplete.bind(this);
            return methods._formSubmitHelper.call(this, event, callback);
        },

        /**
         * DOM handler for when the confirm button is clicked for item
         * deletion.s
         */
        _onDeleteFormSubmitClick : function(event) {
            var callback = methods._onDeleteFormSubmitComplete.bind(this);
            return methods._formSubmitHelper.call(this, event, callback);
        },

        /**
         *
         */
        _onAddFormCancelClick : function(event) {
            event.preventDefault();
            return $(this).fadeOut('fast', methods._onDisabled.bind(this));
        },

        /**
         * DOM handler for when the cancel button on any of the forms
         * (add/remove/edit) is clicked.
         */
        _onEditFormCancelClick : function(event) {
            event.preventDefault();
            var editor = $(this).find('.of-content:first > .of-edit');
            editor.slideUp('fast', methods._onEditorDisabled.bind(this));
        },

        /**
         * DOM handler for when the cancel button on any of the forms
         * (add/remove/edit) is clicked.
         */
        _onDeleteFormCancelClick : function(event) {
            event.preventDefault();
            var editor = $(this).find('.of-content:first > .of-edit');
            editor.slideUp('fast', methods._onEditorDisabled.bind(this));
        },

        /**
         * XHR event when the form data is submitted and a response is returned.
         */
        _onAddFormSubmitComplete : function(response, status, xhr) {
            if (status != 'success') {
                alert('Failed to save changes!!!.');
            } else {
                methods._refresh.call(this, response);
                var settings = $(this).data('formItem');
                $(this).formItem(settings);

                // Very quick, disgusting, shameful hack that needs reworking
                if ($(this).hasClass('of-fieldset')) {
                    // Setup the item's parent listing as a sortable
                    $(this).find('.of-fields').sortable({
                        axis : 'y',
                        containment : '#of-editor',
                        connectWith : '.of-fields',
                        cursor : 'move',
                        forcePlaceholderSize : false,
                        placeholder : 'of-placeholder',
                        items : '.of-field',
                        opacity : 0.6,
                        receive : methods._onReceived,
                        update : methods._onMoved,
                    });
                }
            }
        },

        /**
         * XHR event when the form data is submitted and a response is returned.
         */
        _onEditFormSubmitComplete : function(response, status, xhr) {
            if (status != 'success') {
                alert('Failed to save changes!!!.');
            } else {
                methods._refresh.call(this, response);
            }
        },

        /**
         * XHR handler for when the confirm delete request is completed
         */
        _onDeleteFormSubmitComplete : function(response, status, xhr) {
            if (status != 'success') {
                alert('Failed to delete item :(');
            } else {
                $(this).fadeOut('fast', methods._onDisabled.bind(this));
            }
            return this;
        },

        /**
         * jQuery handler for when this list receives a new item from another
         * list.
         *
         * In some cases it will be a new item, in which a request is made to
         * create one.
         *
         * Only handle items coming from a draggable source
         *
         * Unfortunately, jQuery UI has a bug where ``ui.item``isn't actually
         * the received item. This only occurs when sorting a dropped item
         * (``conntectToSortable``). So instead, we find any newly dropped
         * items....
         */
        _onReceived : function(event, ui) {
            if (!$(ui.item).hasClass('of-item')) {
                var settings = $(ui.item).data('formItem');
                var dropped = $(this).find('.ui-draggable').first();
                var newField = $('#of-item-template .of-item').clone();
                var url = $.trim($(dropped).attr('href'));
                var type = (/add-(\w+)/gi).exec(url)[1];
                var itemSelector = $(this).sortable('option', 'items');
                var itemClass = itemSelector.substring(1);
                var callback = methods._onAddFormLoad.bind(newField);
                var data = {order: dropped.index()};

                var sortable = $(this).closest('.of-item');

                // Need to add traversing to fieldsets
                if (sortable.hasClass('of-fieldset')) {
                    url = url.slice(0, url.lastIndexOf('/'));
                    url += '/' + sortable.attr('dataset').name + '/@@add-' + type;
                }

                newField.addClass(itemClass).addClass(type);
                newField.find('.of-type').first().text(type);
                newField.find('.of-name').first().text('[...]');

                $(newField).data('formItem', settings);
                methods._enableEditor.call(newField, url, data, callback);
                $(dropped).replaceWith(newField);
            }
        },

        /**
         * jQuery handler for when an item from this list is moved.
         */
        _onMoved : function(event, ui) {
            if (event.target === ui.item.parent()[0]) {
                var callback = methods._onMoveComplete.bind(event.target);
                var url = null;
                var target = $(event.target).closest('.of-item').attr('dataset').name;
                var position = $(ui.item).index();
                var data = {
                    'form.widgets.target': target,
                    'form.widgets.order': position,
                    'form.buttons.apply': 1,
                    };

                if (ui.sender) {
                    var itemName = $(ui.item).attr('dataset').name;
                    url = methods.url.call(ui.sender) + itemName;
                } else {
                    url = methods.url.call(ui.item);
                }

               console.log(url, data);
               $.post(url + '/@@order', data, callback);
            }
        },

        _onMoveComplete: function(reponse, status, xhr) {
            if (status != 'success') {
                alert('Failed to sort item :(');
                $(this).sortable('cancel');
            }
            return this;
        },
    };

    /**
     * jQuery plug-in registration for for items. Unless otherwise specified,
     * ``this`` always refers to the individual item.
     */
    $.fn.formItem = function(method) {
        // plug-in boiler plate for determining what method to call.
        if (methods[method]) {
            var parameters = Array.prototype.slice.call(arguments, 1);
            return methods[method].apply(this, parameters);
        } else if (typeof method === 'object' || !method) {
            return methods._initialize.apply(this, arguments);
        } else {
            $.error('Method ' + method + ' does not exist on form item.');
        }

    };

})(jQuery);
