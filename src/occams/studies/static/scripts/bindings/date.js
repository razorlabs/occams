ko.bindingHandlers.datetimeText = {
  update: function(element, valueAccessor, allBindingsAccessor) {
   var value = ko.utils.unwrapObservable(valueAccessor())
     , formattedValue = moment(value).format('llll');
    ko.bindingHandlers.text.update(element, function() { return formattedValue; });
  }
};

ko.bindingHandlers.dateText = {
  update: function(element, valueAccessor, allBindingsAccessor) {
   var value = ko.utils.unwrapObservable(valueAccessor())
     , formattedValue = moment(value).format('ll');
    ko.bindingHandlers.text.update(element, function() { return formattedValue; });
  }
};
