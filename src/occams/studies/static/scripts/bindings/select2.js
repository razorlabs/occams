/**
 * knockout bindings for select2
 * Original:
 * https://github.com/ivaynberg/select2/wiki/Knockout.js-Integration
 * Better version:
 * http://www.davidyardy.com/davidyardy/blog/post/2014/01/20/Select2-and-Knockout-Binding.aspx
 */
ko.bindingHandlers.select2 = {
  init: function (element, valueAccessor, allBindings) {
    var obj = valueAccessor()
      , lookupKey = allBindings.get('lookupKey');

    $(element).select2(obj);

    // Need special binding parameter for ajax-multiselects
    if (allBindings.has('selectedValues')){
      var selectedValues = allBindings.get('selectedValues');
      $(element).select2('val', ko.unwrap(selectedValues).join(','));
      $(element).on('change', function(){
        selectedValues($(this).select2('val'));
      });
    }

    // Ensure the select2 blur event triggers the orginal element's blur event
    // (Not sure why it doesn't do this in the first place...)
    $(element).on('select2-blur', function() {
      $(this).trigger('focusout');
    });

    if (lookupKey) {
      var value = ko.unwrap(allBindings.value);
      $(element).select2('data', ko.utils.arrayFirst(obj.data.results, function (item) {
        return item[lookupKey] === value;
      }));
    }

    ko.utils.domNodeDisposal.addDisposeCallback(element, function () {
      $(element).select2('destroy');
    });
  },
  update: function (element, valueAccessor, allBindings) {
    $(element).trigger('change');
  }
};
