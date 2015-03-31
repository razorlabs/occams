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
    data = data || {};
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

  self.update(data);
}
