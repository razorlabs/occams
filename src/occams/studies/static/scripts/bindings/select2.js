/**
 * knockout bindings for select2
 * Original:
 * https://github.com/ivaynberg/select2/wiki/Knockout.js-Integration
 * Better version:
 * http://www.davidyardy.com/davidyardy/blog/post/2014/01/20/Select2-and-Knockout-Binding.aspx
 */
ko.bindingHandlers.select2 = {
  init: function (element, valueAccessor, allBindingsAccessor) {
    var obj = valueAccessor()
      , allBindings = allBindingsAccessor()
      , lookupKey = allBindings.lookupKey;

    $(element).select2(obj);

    if (lookupKey) {
      var value = ko.utils.unwrapObservable(allBindings.value);
      $(element).select2('data', ko.utils.arrayFirst(obj.data.results, function (item) {
        return item[lookupKey] === value;
      }));
    }

    ko.utils.domNodeDisposal.addDisposeCallback(element, function () {
      $(element).select2('destroy');
    });
  },
  update: function (element) {
    $(element).trigger('change');
  }
};
