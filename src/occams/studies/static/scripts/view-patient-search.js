function PatientSearchView(){
  "use strict";
  var self = this;

  self.isReady = ko.observable(false);

  self.results = ko.observableArray(JSON.parse($('#results-data').text()));

  self.hasResults = ko.computed(function(){
    return self.results().length > 0;
  });

  self.isReady(true);
}


+function($){
  "use strict";
  $(document).ready(function(){
    var $view = $('#views-patient-search')[0];
    if ($view){
      ko.applyBindings(new PatientSearchView(), $view);
    }
  });
}(jQuery);
