/**
 * Form field manager view model
 */
function VersionViewModel(){
  'use strict';

  var self = this;

  self.isReady = ko.observable(true);        // content loaded flag

  self.isDrafting = ko.observable(false);
  self.isDeleting = ko.observable(false);

  self.showDraftView = ko.observable(false);
  self.showDeleteView = ko.observable(false);

  // We don't load anything so we need to inspect the
  // contents for the source targets
  self.deleteSrc = $('#delete-button').data('target');
  self.draftSrc = $('#delete-button').data('target');

  self.clearSelected = function(){
    self.showDeleteView(false);
    self.showDraftView(false);
  };

  self.startDraftView = function(){
    self.clearSelected();
    self.showDraftView(true);
  };

  self.startDeleteView = function() {
    self.clearSelected();
    self.showDeleteView(true);
  };

  /**
   * Sends a draft request for the current version of the form.
   */
  self.doDraftForm = function(form){
    self.isDrafting(true);
    $.ajax({
      url: self.draftSrc,
      method: 'POST',
      data: {draft: 1},
      headers: {'X-CSRF-Token': $.cookie('csrf_token')},
      error: function(jqXHR, textStatus, errorThrown){
        console.log('An error occurred, need to show something...');
      },
      success: function(data, textStatus, jqXHR){
        window.location = data.__next__;
      }
    });
  };

  /**
   * Sends a delete request for the current version of the form.
   */
  self.doDeleteForm = function(form){
    self.isDeleting(true);
    $.ajax({
      url: self.deleteSrc,
      method: 'DELETE',
      headers: {'X-CSRF-Token': $.cookie('csrf_token')},
      error: function(jqXHR, textStatus, errorThrown){
        console.log('An error occurred, need to show something...');
      },
      success: function(data, textStatus, jqXHR){
        window.location = data.__next__;
      }
    });
  };
}
