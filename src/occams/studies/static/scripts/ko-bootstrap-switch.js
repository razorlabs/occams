/**
 * https://github.com/pauloortins/knockout-bootstrap-switch
 */
ko.bindingHandlers.bootstrapSwitch = {
  init: function (element, valueAccessor, allBindings) {
    //initialize bootstrapSwitch
    $(element).bootstrapSwitch();

    // handle the field changing
    $(element).on('switchChange.bootstrapSwitch', function (event, state) {
      var observable = valueAccessor();
      observable(state);
    });

    //handle disposal (if KO removes by the template binding)
    ko.utils.domNodeDisposal.addDisposeCallback(element, function () {
      $(element).bootstrapSwitch('destroy').remove();
    });
  },

  //update the control when the view model changes
  update: function (element, valueAccessor, allBindings) {

    // Adding component options
    if (allBindings.has('bootstrapSwitchOptions')){
      for (var property in allBindings.get('bootstrapSwitchOptions')){
        $(element).bootstrapSwitch(property, ko.unwrap(options[property]));
      }
    }

    $(element).bootstrapSwitch('state', ko.unwrap(valueAccessor()));
  }
};
