function ExternalServicesView(options){
  'use strict'

  var self = this;

  self.isReady = ko.observable(false);      // Indicates UI is ready
  self.isSaving = ko.observable(false);     // Indicates AJAX call
  self.isUploading = ko.observable(false);

  self.selectedService = ko.observable(false);

  self.externalServices = ko.observableArray();

  // Modal states
  var VIEW = 'view', EDIT = 'edit',  DELETE = 'delete';

  self.hasExternalServices = ko.pureComputed(function(){
    return self.externalServices().length > 0
  });

  $.getJSON(options.serviceUrl, function(data){
      self.externalServices(data.external_services.map(function(rawData){
        return new ExternalService(rawData)
      }));

      self.isReady(true);
    });

  self.startEditExternalService = function(service, event){
    self.selectedService(service);
    self.editableService(new ExternalService(ko.toJS(service)));
    self.studyModalState(EDIT);
  };

  self.startDeleteExternalService = function(service, event){
    self.selectedService(service);
    self.studyModalState(DELETE);
  };
}