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

  self.update = function(data){
    self.__url__(data.__url__);
    self.name(data.name);
    self.title(data.title);
    self.short_title(data.short_title);
    self.code(data.code);
    self.consent_date(data.consent_date);
    self.start_date(data.start_date);
    self.end_date(data.end_date);
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
  self.searchParams = function(term, page){
    return {vocabulary: 'available_schemata', term: term};
  };

  // Select2 termination results callback
  self.searchResults = function(data){
    return {
      results: data.schemata.map(function(schema){
        return new StudyForm({schema: schema, versions: [schema]});
      })
    };
  };

  self.update(data || {});
}


/**
 *
 */
function StudyForm(data){
  'use strict';

  var self = this;

  self.isNew = ko.observable();

  self.schema = ko.observable();
  self.versions = ko.observableArray();

  // Short-hand name getter
  self.name = ko.pureComputed(function(){
    return self.schema() && self.schema().name;
  });

  // Short-hand title getter
  self.title = ko.pureComputed(function(){
    return self.schema() && self.schema().title;
  });

  self.titleWithVersion = ko.computed(function(){
    if (self.versions().length == 1){
      var version = self.versions()[0];
      return version.title + ' @ ' + version.publish_date;
    }
  });

  self.update = function(data){
    self.isNew(data.isNew || false);
    self.schema(data.schema || null);
    self.versions(data.versions || []);
  };

  self.hasMultipleVersions = ko.computed(function(){
    return self.versions().length > 1;
  });

  self.versionsLength = ko.computed(function(){
    return self.versions().length;
  });

  // Select2 schema search parameters callback
  self.searchSchemaParams = function(term, page){
    return {vocabulary: 'available_schemata', term: term, grouped: true};
  };

  // Select2 schema results callback
  self.searchSchemaResults = function(data){
    return {results: data.schemata.map(function(item){ return item.schema; })};
  };

  // Select2 version search parameters callback
  self.searchVersionsParams = function(term, page){
    return {vocabulary: 'available_schemata', term: term, schema: self.schema().name};
  };

  // Select2 version results callback
  self.searchVersionsResults = function(data){
    return {results: data.schemata};
  };

  self.update(data || {});
}
