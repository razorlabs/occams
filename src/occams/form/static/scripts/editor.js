/**
 * @fileOverview OCCAMS Form Editor Application
 *
 */

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
        _init : function(options) {
            return this.each(function() {
                var settings = $.extend({
                    containment : null,
                    draggable : null,
                    sortable : null,
                    type : null,
                    placeholder : null,
                }, options);

                var isSortableSetup =
                    $(this).closest(settings.sortable).hasClass('ui-sortable');

                var isDraggableSetup =
                    $(settings.draggable).hasClass('ui-draggable');

                var isDataSetup = $(this).data('formItem');

                // Setup the item's parent listing as a sortable
                if (!isSortableSetup) {
                    $(settings.sortable).sortable({
                        axis : 'y',
                        containment : settings.containment,
                        connectWith : settings.sortable,
                        cursor : 'move',
                        forcePlaceholderSize : false,
                        placeholder : settings.placeholder,
                        items : '.' + settings.type,
                        opacity : 0.6,
                        // stop: jQuery will assign "this" to the new element
                        stop : methods._onDropped,
                        receive : methods._onReceived.bind(this),
                        update : methods._onMoved.bind(this),
                    });
                }

                // Configure types as draggable, this is how the user will add
                // new fields to a form. Also, using ``connectToSortable``, we
                // can add it to the fields listing. We handle new fields using
                // the sortable's ``receive`` event because using droppable's
                // ``drop`` triggers duplicate events, a known jQuery bug.
                if (!isDraggableSetup) {
                    $(settings.draggable).draggable({
                        containment : settings.containment,
                        connectToSortable : settings.sortable,
                        cursor : 'move',
                        helper : 'clone',
                        revert : 'invalid',
                        zIndex : 9001,
                    });
                }

                // Finally, configure the actual item
                if (!isDataSetup) {
                    $(this).data('formItem', settings);
                    var head = $(this).children('.of-head');
                    var controls = head.find('.of-controls');
                    var collapseButton = head.find('.of-collapseable');
                    var editButton = controls.find('a.of-editable');
                    var deleteButton = controls.find('a.of-deleteable');
                    editButton.click(methods._onEditClick.bind(this));
                    deleteButton.click(methods._onDeleteClick.bind(this));
                    collapseButton.click(methods._onCollapseClick.bind(this));
                }
            });
        },

        /**
         * Refreshes the the item with new incoming data
         * @param data  json data to refresh the item with
         */
        _refresh : function(data) {
            var view = $(this).find('.of-content:first > .of-view');
            var edit = $(this).find('.of-content:first > .of-edit');

            $(this).find('.of-name').first().text(data.name);
            $(this).find('.of-title').first().text(data.title);
            $(this).find('.of-version').first().text(data.version);
            $(this).find('.of-description').first().text(data.description);

            if (data.view) {
                var newField = $(data.view).find('#form');
                view.empty().append(newField);
            }

            edit.slideUp('fast', methods._onEditorDisabled.bind(this));
            return this;
        },

        /**
         *
         */
        _enableEditor : function(url, next) {
            var selector = $.trim(url) + ' #form';
            $(this).find('.of-content:first > .of-edit').load(selector, next);
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
                var action = actions[button.attr('name')];
                if (action) {
                    button.click(action);
                }
            });

            // Run datagridfield's setup, since it assumes the DOM was already
            // there, but it's not because we dynamically load it.
            // Also fix it so that it triggers when the actual input element is
            // changed.
            $(this).find('.auto-append > .datagridwidget-cell input').change(
                    dataGridField2Functions.autoInsertRow);

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
            var viewer = $(this).find('.of-content:first > .of-view');
            var url = form.attr('action')
            var data = form.serializeArray();
            data.push({
                name : $(event.target).attr('name'),
                value : $(event.target).attr('value')
            });
            // Disable the submit button so the user doesn't go click-happy
            $(event.target).attr({
                disabled : 'disabled',
                value : 'Thinking...'
            });
            $.post(url, data, callback, 'json');
            return this;
        },

        _onCollapseClick : function(event) {
            event.preventDefault();
            $(this).find('.of-content:first').slideToggle('fast');
            return this;
        },

        /**
         *
         */
        _onEditClick : function(event) {
            event.preventDefault();
            var url = $(event.target).attr('href');
            return methods._enableEditor.call(this, url,
                    methods._onEditFormLoad.bind(this));
        },

        /**
         *
         */
        _onDeleteClick : function(event) {
            event.preventDefault();
            var url = $(event.target).attr('href')
            return methods._enableEditor(url, methods._onDeleteFormLoad
                    .bind(this))
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
                    'form.buttons.add' : methods._onAddFormSubmitClick
                            .bind(this),
                    'form.buttons.cancel' : methods._onAddFormCancelClick
                            .bind(this),
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
                alert('An error has occured while trying to load the edit form');
            } else {
                methods._formSetupHelper.call(this, {
                    'form.buttons.apply' : methods._onEditFormSubmitClick
                            .bind(this),
                    'form.buttons.cancel' : methods._onEditFormCancelClick
                            .bind(this),
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
                alert('An error has occured while trying to load the delete form');
            } else {
                methods._formSetupHelper.call(this, {
                    'form.buttons.delete' : methods._onDeleteFormSubmitClick
                            .bind(this),
                    'form.buttons.cancel' : methods._onDeleteFormCancelClick
                            .bind(this),
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
            return methods._remove.call(this);
        },

        /**
         * DOM handler for when the cancel button on any of the forms
         * (add/remove/edit) is clicked.
         */
        _onEditFormCancelClick : function(event) {
            event.preventDefault();
            $(this).find('.of-content:first > .of-edit').slideUp('fast',
                    methods._onEditorDisabled.bind(this));
        },

        /**
         * DOM handler for when the cancel button on any of the forms
         * (add/remove/edit) is clicked.
         */
        _onDeleteFormCancelClick : function(event) {
            event.preventDefault();
            $(this).find('.of-content:first > .of-edit').slideUp('fast',
                    methods._onEditorDisabled.bind(this));
        },

        /**
         * XHR event when the form data is submitted and a response is returned.
         */
        _onAddFormSubmitComplete : function(response, status, xhr) {
            if (status != 'success') {
                alert('Failed to save changes!!!.');
            } else {
                methods._refresh.call(this, response)
            }
        },

        /**
         * XHR event when the form data is submitted and a response is returned.
         */
        _onEditFormSubmitComplete : function(response, status, xhr) {
            if (status != 'success') {
                alert('Failed to save changes!!!.');
            } else {
                methods._refresh.call(this, response)
            }
        },

        /**
         * XHR handler for when the confirm delete request is completed
         */
        _onDeleteFormSubmitComplete : function(response, status, xhr) {
            if (status != 'success') {
                alert('Failed to delete item :(');
            } else {
                methods._disableItem().call(this);
            }
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
        _onDropped : function(event, ui) {
            var isDraggable = $(ui.item).hasClass('ui-draggable');
            if (isDraggable) {
                var newField = $('#of-item-template .of-item').clone();
                var url = $.trim($(ui.item).attr('href')) + ' #form';
                var type = (/add-(\w+)/gi).exec(url)[1];
                var itemClass = $(this).sortable('option', 'items').substring(1);
                var callback = methods._onAddFormLoad.bind(newField);
                var data = {order: ui.item.index() + 1};

                newField.addClass(itemClass).addClass(type);
                newField.find('.of-type').first().text(type);
                newField.find('.of-name').first().text('[...]');
                newField.find('.of-edit').load(url, data, callback);

                $(ui.item).replaceWith(newField);
            }
        },

        /**
         *
         */
        _onReceived : function(event, ui) {
            var isDraggable = $(ui.item).hasClass('ui-draggable');
            // Only handle items sortable items
            if (!isDraggable) {
                console.log('received');
                console.log($(ui.item));
            }
        },

        /**
         * jQuery handler for when an item from this list is moved elsewhere.
         */
        _onMoved : function(event, ui) {
            var isDraggable = $(ui.item).hasClass('ui-draggable');
            var isReceived = ui.sender || event.target !== ui.item.parent()[0];
            // Only handle items sortable items
            if (!isDraggable && !isReceived) {
                console.log('moved');
                console.log($(ui.item));
            }
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
            return methods._init.apply(this, arguments);
        } else {
            $.error('Method ' + method + ' does not exist on form item.');
        }
    };

})(jQuery);

/**
 * @class jQuery Form Editor Application Plug-in
 */
(function($) {
    'use strict';

    var methods = {
        _init : function(options) {
            return this.each(function() {
                // Fieldset Items
                $('.of-fieldset').formItem({
                    containment : '#of-editor',
                    sortable : '#of-fieldsets',
                    placeholder : 'of-placeholder',
                    draggable : '#of-new l a:has([class="object"])',
                    type : 'of-fieldset',
                });

                // Field Items
                $('.of-field').formItem({
                    containment : '#of-editor',
                    sortable : '.of-fields',
                    placeholder : 'of-placeholder',
                    draggable : '#of-new li a:not(:has([class="object"]))',
                    type : 'of-field',
                });

                // Disable type links so we don't navigate to them
                $('#of-new li a').each(function() {
                    $(this).click(function(event) {
                        event.preventDefault();
                    });
                });

                // Setup the types element as a floating panel (because the
                // forms can -- and will -- get pretty long)
                $(window).scroll(function(event) {
                    var panel = $('#of-aux');
                    var container = $('#of-editor');
                    var containerOffset = container.offset();
                    var scrollY = $(window).scrollTop();

                    // Reposition if the window if the scrolling
                    // position is past the editor
                    // Note that we only need to re-render if it hasn't
                    // been set yet.
                    if (scrollY >= containerOffset.top) {
                        if (panel.css('position') != 'fixed') {
                            var right =
                                $(window).width() - (panel.offset().left + panel.width());
                            panel.css({
                                position : 'fixed',
                                top : 0,
                                right : right + 'px'
                            });
                        }
                    } else {
                        if (panel.css('position') != 'absolute') {
                            panel.css({
                                position : 'absolute',
                                top : 0,
                                right : 0
                            });
                        }
                    }
                });
            });
        }
    };

    /**
     * jQuery plug-in registration for for items. Unless otherwise specified,
     * ``this`` always refers to the individual item.
     */
    $.fn.formEditor = function(method) {
        // plug-in boiler plate for determining what method to call.
        if (methods[method]) {
            var parameters = Array.prototype.slice.call(arguments, 1);
            return methods[method].apply(this, parameters);
        } else if (typeof method === 'object' || !method) {
            return methods._init.apply(this, arguments);
        } else {
            $.error('Method ' + method + ' does not exist on form item.');
        }
    };

})(jQuery);

/**
 * Application bootstrap
 */
(function($) {
    'use strict';
    $(document).ready(function() {
        $('#of-editor').formEditor();
    });
})(jQuery);
