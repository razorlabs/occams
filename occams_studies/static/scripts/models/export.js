/**
 * An individual Export model
 */
function Export(data) {
  'use strict';

  var self = this;

  self.id = ko.observable();
  self.title = ko.observable();
  self.name = ko.observable();
  self.status = ko.observable();
  self.use_choice_labels = ko.observable();
  self.expand_collections = ko.observable();
  self.contents = ko.observable();
  self.count = ko.observable();
  self.total = ko.observable();
  self.file_size = ko.observable();
  self.download_url = ko.observable();
  self.delete_url = ko.observable();
  self.create_date = ko.observable();
  self.expire_date = ko.observable();

  self.update = function(data){
    data = data || {};
    self.id(data.id);
    self.title(data.title);
    self.name(data.name);
    self.status(data.status);
    self.use_choice_labels(data.use_choice_labels);
    self.expand_collections(data.expand_collections);
    self.contents(data.contents);
    self.count(data.count);
    self.total(data.total);
    self.file_size(data.file_size);
    self.download_url(data.download_url);
    self.delete_url(data.delete_url);
    self.create_date(data.create_date);
    self.expire_date(data.expire_date);
  };

  /**
   * Calculates this export's current progress
   */
  self.progress = ko.pureComputed(function(){
    return Math.ceil((self.count() / self.total()) * 100);
  }).extend({ throttle: 1 });

  self.update(data);
}

