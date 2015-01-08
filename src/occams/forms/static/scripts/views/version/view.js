/**
 * Form field manager view model
 */
function VersionViewModel(options){
  'use strict';

  var self = this;

  self.isReady = ko.observable(false);        // content loaded flag
  self.isSaving = ko.observable(false);

  self.errorMessage = ko.observable();
  self.successMessage = ko.observable();

  self.version = ko.observable();
  self.editableVersion = ko.observable();

  var DRAFT = 'draft', PUBLISH = 'publish', DELETE = 'delete';

  self.mode = ko.observable()
  self.showDraft = ko.pureComputed(function(){ return self.mode() == DRAFT; });
  self.showPublish = ko.pureComputed(function(){ return self.mode() == PUBLISH; });
  self.showDelete = ko.pureComputed(function(){ return self.mode() == DELETE; });

  self.clear = function(){
    self.mode(null);
    self.editableVersion(null);
    self.errorMessage(null);
  };

  self.startDraftVersion = function(){
    self.mode(DRAFT);
  };

  self.startPublishVersion = function(){
    self.editableVersion(new Version(ko.toJS(self.version())));
    self.mode(PUBLISH);
  };

  self.startDeleteVersion = function() {
    self.mode(DELETE);
  };

  /**
   * Sends a draft request for the current version of the form.
   */
  self.draftVersion = function(element){
    $.ajax({
      url: options.versionUrl,
      method: 'POST',
      data: {draft: 1},
      headers: {'X-CSRF-Token': $.cookie('csrf_token')},
      error: handleXHRError({logger: self.errorMessage}),
      beforeSend: function(){
        self.isSaving(true);
      },
      success: function(data, textStatus, jqXHR){
        window.location = data.__next__;
      },
      complete: function(){
        self.isSaving(false);
      }
    });
  };

  self.publishVersion = function(element){
    if ($(element).validate().form()){
      var edits = ko.toJS(self.editableVersion());
      $.ajax({
        url: options.versionUrl + '?publish',
        method: 'PUT',
        data: ko.toJSON({
          publish_date: edits.publish_date,
          retract_date: edits.retract_date
        }),
        contentType: 'application/json; charset=utf-8',
        headers: {'X-CSRF-Token': $.cookie('csrf_token')},
        error: handleXHRError({form: element, logger: self.errorMessage}),
        beforeSend: function(){
          self.isSaving(true);
        },
        success: function(data, textStatus, jqXHR){
          // The models are currently not ready for partial updates,
          // set the values individually...
          var version = self.version();
          version.publish_date(data.publish_date);
          version.retract_date(data.retract_date);
          self.successMessage("Sucessfully updated publication dates");
          self.clear();
        },
        complete: function(){
          self.isSaving(false);
        }
      });
    }
  };

  /**
   * Sends a delete request for the current version of the form.
   */
  self.deleteVersion = function(form){
    $.ajax({
      url: options.versionUrl,
      method: 'DELETE',
      headers: {'X-CSRF-Token': $.cookie('csrf_token')},
      error: handleXHRError({logger: self.errorMessage}),
      beforeSend: function(){
        self.isSaving(true);
      },
      success: function(data, textStatus, jqXHR){
        window.location = data.__next__;
      },
      complete: function(){
        self.isSaving(false);
      }
    });
  };

  $.getJSON(options.versionUrl, function(data){
    self.version(new Version(data));
    self.isReady(true);
  });
}
