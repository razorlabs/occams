function Study(data){
  'use strict';

  var self = this;

  self.__url__ = ko.observable();

  self.id = ko.observable();
  self.name = ko.observable();
  self.title = ko.observable();
  self.short_title = ko.observable();
  self.code = ko.observable();
  self.consent_date = ko.observable();
  self.start_date = ko.observable();
  self.end_date = ko.observable();
  self.termination_form = ko.observable();
  self.is_randomized = ko.observable();
  self.is_blinded = ko.observable();
  self.reference_pattern = ko.observable();
  self.reference_hint = ko.observable()
  self.randomization_form = ko.observable();

  self.forms = ko.observableArray();
  self.cycles = ko.observableArray();

  // Easier access to enrollment-desigated forms
  // this will go away when all forms are done via studies
  self.enrollmentForms = ko.pureComputed(function(){
    var forms = [];
    if (self.termination_form()){
      forms.push(self.termination_form());
    }
    if (self.randomization_form()){
      forms.push(self.randomization_form());
    }
    return forms;
  });

  self.isNew = ko.pureComputed(function(){
    return !self.id();
  });

  self.update = function(data){
    data = data || {};
    self.__url__(data.__url__);
    self.id(data.id);
    self.name(data.name);
    self.title(data.title);
    self.short_title(data.short_title);
    self.code(data.code);
    self.consent_date(data.consent_date);
    self.start_date(data.start_date);
    self.end_date(data.end_date);
    self.reference_pattern = ko.observable(data.reference_pattern);
    self.reference_hint = ko.observable(data.reference_hint);
    self.termination_form(data.termination_form ? new StudyForm(data.termination_form) : null);
    self.is_randomized(data.is_randomized);
    self.is_blinded(data.is_blinded);
    self.randomization_form(data.randomization_form ? new StudyForm(data.randomzation_form) : null);
    self.forms((data.forms || []).map(function(value){
      return new StudyForm(value);
    }));
    self.cycles((data.cycles || []).map(function(value){
      return new Cycle(value);
    }));

    self.forms.sort(function(a, b){
      return a.title().localeCompare(b.title());
    });

    self.cycles.sort(function(a, b){
      a = parseInt(ko.unwrap(a.week));
      b = parseInt(ko.unwrap(b.week));
      if (!isNaN(a) && isNaN(b)){
        return -1;
      } else if (isNaN(a) && !isNaN(b)){
        return 1;
      } else {
        return a - b;
      }
    });
  };

  // Select2 termination search parameters callback
  // TODO: How is this one different from the one in study.js?
  self.searchParams = function(term, page){
    return {vocabulary: 'available_schemata', term: term};
  };

  // Select2 termination results callback
  // TODO: How is this one different from the one in study.js?
  self.searchResults = function(data){
    return {
      results: data.schemata.map(function(schema){
        return new StudyForm({schema: schema, versions: [schema]});
      })
    };
  };

  self.update(data);
}
