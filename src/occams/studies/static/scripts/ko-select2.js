/**
 * Knockout bindings for Select2 UI element
 *
 * Adapted from:
 * https://github.com/ivaynberg/select2/wiki/Knockout.js-Integration
 */

+function(){
  "use strict";

  /**
   * Binding handler for Select 2 UI element
   *
   * If used on a <select> element, this binding will try to reuse
   * exsiting Knockout bindings to configure the select 2 instnace.
   *
   * For custom ajax functionality, you'll need to set the ``selectedData``
   * binding (as using "value" interferes with processing). Also,
   * you'll need to configure ``select2``  with the following parameters:
   *  * ``multiple`` -- true/false
   *  * ``query`` or ``ajax`` -- if using dynamic options
   *  * ``formatResult`` --  formats the selected object into a select2 user label
   *  * ``formatSelection`` -- format the selected object into a select2 text
   *
   *  In most cases ``formatResult`` and ``formatSelection`` can be the same
   *  function that just returns a string label. If you desire extra control,
   *  add extra markup in the ``formatResult`` function.
   *
   */
  ko.bindingHandlers.select2 = {

    init: function(element, valueAccessor, allBindings, viewModel) {
      // Dispose configurations when this element is removed
      ko.utils.domNodeDisposal.addDisposeCallback(element, function() {
        $(element).select2('destroy');
      });

      var select2Settings = ko.unwrap(allBindings.get('select2'));

      if (allBindings.has('dataId')){
        $.extend(select2Settings, {
          id: function(item){
            return ko.unwrap(item[allBindings.get('dataId')]);
          }
        });
      }

      if (allBindings.has('dataLabel')){
        var getLabel = function(item){
          return ko.unwrap(item[allBindings.get('dataLabel')]);
        };
        $.extend(select2Settings, {
          formatSelection: getLabel,
          formatResult: getLabel,
        });
      }

      $(element)
        .select2(select2Settings)
        .on('select2-blur', function(){
          // Trigger focusout on underlying element for validation
          $(this).trigger('focusout');
        });

      // Remember to update the attached binding
      if (allBindings.has('selectedData')){
        var dataAccessor = allBindings.get('selectedData');
        $(element).on('change', function(){
          dataAccessor($(element).select2('data'));
        });
      }
    },

    update: function (element, valueAccessor, allBindings, viewModel) {

      if (allBindings.has('enable')){
         $(element).select2('enable', !!ko.unwrap(allBindings.get('enable')));
      }

      if (allBindings.has('disable')){
         $(element).select2('enable', !ko.unwrap(allBindings.get('disable')));
      }

      // Regular HTML value
      if (allBindings.has('value')){
        $(element).select2('val', ko.unwrap(allBindings.get('value')));

      // Advanced JS objects selection
      } else if (allBindings.has('selectedData')){
        $(element).select2('data', ko.unwrap(allBindings.get('selectedData')));

      // Regualr Knockout bindings on a <select> element
      } else if (allBindings.has('selectedOptions')){
        var textAccessor; // callback for determining value label

        if (allBindings.has('optionsText')){
          textAccessor = function(value) {
            var valueAccessor; // callback for termining selected value

            if (allBindings.has('optionsValue')){
              valueAccessor = function (item) {
                return item[ko.unwrap(allBindings.get('optionsValue'))];
              };
            } else {
              valueAccessor = function (item) { return item; };
            }

            var items = ko.unwrap(allBindings.get('options')).filter(function(e){
              return valueAccessor(e) == value
            });

            if (items.length != 1){
              return 'UNKNOWN'; // Need exactly one value
            } else {
              return items[0][ko.unwrap(allBindings.get('optionsText'))];
            }
          }
        } else {
          textAccessor = function(value) { return value; };
        }

        $(element).select2('data', ko.unwrap(allBindings.get('selectedOptions')).map(function(value){
          return {id: value, text: textAccessor(value)};
        }));
      }

      // Let listeners know that things have changed
      $(element).trigger('change');
    }
  };

}();
