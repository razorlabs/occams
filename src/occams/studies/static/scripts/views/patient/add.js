function PatientAddView(){
  'use strict';

  var self = this;

  self.isReady = ko.observable(false);
  self.isSaving = ko.observable(false);

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

  self.savePatient = function(form){
  };

  self.isReady(true);
}
