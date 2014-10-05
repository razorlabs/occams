function PatientSearchView(){
  "use strict";
  var self = this;

  self.isReady = ko.observable(false);
  self.isLoading = ko.observable(false);

  // Search terms
  self.query = ko.observable();

  self.hasPrevious = ko.observable(false);

  // Parameters for traversing to the previous page
  self.previousParams = function(){
    return {query: self.query(), page: self.page() - 1};
  };

  // URL form of previous paramters
  self.previousUrl = function(){
    return '?' + $.param(self.previousParams(), true);
  };

  self.hasNext = ko.observable(false);

  // Parameters for traversing the the next page
  self.nextParams = function(){
    return {query: self.query(), page: self.page() + 1};
  };

  // URL form of next pareters
  self.nextUrl = function(){
    return '?' + $.param(self.nextParams(), true);
  };

  // Current result page
  self.page = ko.observable();

  // Loaded results
  self.results = ko.observableArray([]);

  self.hasResults = ko.computed(function(){
    return self.results().length > 0;
  });

  self.showPager = ko.computed(function(){
    return self.hasNext()|| self.hasPrevious();
  });

  /**
   * Helper function to load results from an AJAX request
   */
  self.update = function(data){
    // Group enrollments by study so they're not redundant in the page
    data.patients.forEach(function(patient){
      patient.groupedEnrollments = groupBy(patient.enrollments || [], function(enrollment){
        return [enrollment.study.title, enrollment.reference_number];
      }).map(function(group){;
        return {
          studyTitle: group[0].study.title,
          reference_number: group[0].reference_number,
          group: group
        };
      });
    });
    self.results(data.patients);
    self.hasPrevious(data.__has_previous__);
    self.hasNext(data.__has_next__);
    self.page(data.__page__);
    self.query(data.__query__);
  };

  /**
   * Loads new result terms
   */
  self.onSubmitSearch = function(){
    // Attempt to load via ajax, if not just do a full refresh
    if (!history.pushState){
      return true;
    }

    self.isLoading(true);
    var params = {query: self.query()}
      , url = '?' + $.param(params, true);
    $.get(url, function(data){
      self.update(data);
      history.pushState(params, 1, url);
      self.isLoading(false);
    });
  };

  /**
   * Loads next page of results
   */
  self.onClickNext = function(data, event){
    return self.fetchPage(self.nextParams(), event);
  };

  /**
   * Loads previous page of results
   */
  self.onClickPrevious = function(data, event){
    return self.fetchPage(self.previousParams(), event);
  };

  /**
   * Helper method for loading page results
   */
  self.fetchPage = function(params, event){

    // Attempt to load via ajax, if not just do a full refresh
    if (!history.pushState){
      return true;
    }

    self.isLoading(true);

    var url = '?' + $.param(params, true);

    $.get(url,  function(data){
      self.update(data);
      history.pushState(params, params['page'], url);
      $(window).scrollTop(0);
      $(event.target).blur();
      self.isLoading(false);
    });
  };

  // When the page is intialized, the server will have
  // already done an initial search (so we don't have to keep waiting)
  self.update(JSON.parse($('#results-data').text()));
  self.isReady(true);
}


+function($){
  "use strict";
  $(document).ready(function(){
    var element = $('#views-patient-search')[0];
    if (element){
      ko.applyBindings(new PatientSearchView(), element);
    }
  });
}(jQuery);
