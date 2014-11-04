function PatientAddView(){
  'use strict';

  var self = this;

  self.isReady = ko.observable(false);
  self.isSaving = ko.observable(false);

  self.errorMessage = ko.observable();

  self.selectedItem = ko.observable();
  self.editableItem = ko.observable();

  var EDIT = 'edit';

  self.statusPatient = ko.observable();
  self.showEditPatient = ko.pureComputed(function(){ return self.statusPatient() == EDIT; });

  self.clear = function(){
    self.selectedItem(null);
    self.editableItem(null);
    self.statusPatient(null);
  };

  self.startAddPatient = function(){
    self.clear();
    self.statusPatient(EDIT);
    self.editableItem(new Patient());
  };

  self.savePatient = function(element){
    if ($(element).validate().form()){
      $.ajax({
        url: $(element).attr('action'),
        method: 'POST',
        contentType: 'application/json; charset=utf-8',
        data: ko.toJSON(self.editableItem()),
        headers: {'X-CSRF-Token': $.cookie('csrf_token')},
        error: handleXHRError({form: element, logger: self.errorMessage}),
        beforeSend: function(){
          self.isSaving(true);
        },
        success: function(data, textStatus, jqXHR){
          window.location = data.__url__
          self.clear();
        },
        complete: function(){
          self.isSaving(false);
        }
      });
    }
  };

  self.isReady(true);
}
