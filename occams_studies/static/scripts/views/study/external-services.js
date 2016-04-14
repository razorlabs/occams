function ExternalServicesView(options){
  'use strict'

  var self = this;

  self.isReady = ko.observable(false);      // Indicates UI is ready
  self.isSaving = ko.observable(false);     // Indicates AJAX call
  self.isUploading = ko.observable(false);

  self.externalServices = ko.observableArray();

  self.externalServices.subscribe(function(){
    self.externalServices.sort(function(a, b){ return a.title().localeCompare(b.title()); });
  });

  self.hasExternalServices = ko.pureComputed(function(){
    return self.externalServices().length > 0
  });

  // Modal states
  var VIEW = 'view', EDIT = 'edit',  DELETE = 'delete';
  self.mode = ko.observable();
  self.inEditMode = ko.pureComputed(function(){ return self.mode() == EDIT; });
  self.inDeleteMode = ko.pureComputed(function(){ return self.mode() == DELETE; });
  self.selectedService = ko.observable();
  self.editableService = ko.observable();

  self.clear = function(){
    self.status(null);
    self.selectedService(null);
    self.editableService(null);
  };

  self.startAddExternalService = function(service, event){
    self.selectedService(new Externalservice());
    self.editableService(new ExternalService());
    self.mode(EDIT);
  };

  self.startEditExternalService = function(service, event){
    self.selectedService(service);
    self.editableService(new ExternalService(ko.toJS(service)));
    self.mode(EDIT);
  };

  self.saveService = function(element){
    if (!$(element).validate().form()){
      return;
    }

    var selected = self.selectedService(),
        editable = self.editableService();

    $.ajax({
      url: selected.isNew() ? options.servicesUrl : selected.__url__(),
      method: selected.isNew() ? 'POST' : 'PUT',
      contentType: 'application/json; charset=utf-8',
      data: ko.toJSON(editable),
      headers: {'X-CSRF-Token': $.cookie('csrf_token')},
      error: handleXHRError({form: element, logger: self.errorMessage}),
      beforeSend: function(){
        self.isAjaxing(true);
      },
      success: function(data){
        self.externalServices.push(new ExternalService(data));
        self.clear();
      },
      complete: function(){
        self.isAjaxing(false);
      }
    });
  };

  self.startDeleteExternalService = function(service, event){
    self.selectedService(service);
    self.mode(DELETE);
  };

  self.deleteService = function(element){
    var selected = self.selectedService();
    $.ajax({
      url: selected.__url__(),
      method: 'DELETE',
      headers: {'X-CSRF-Token': $.cookie('csrf_token')},
      error: handleXHRError({form: element, logger: self.errorMessage}),
      beforeSend: function(){
        self.isAjaxing(true);
      },
      success: function(data){
        self.externalServices.remove(selected);
        self.clear();
      },
      complete: function(){
        self.isAjaxing(false);
      }
    });
  };


  $.getJSON(options.serviceUrl, function(data){
    self.externalServices(data.external_services.map(function(rawData){
      return new ExternalService(rawData)
    }));

    self.isReady(true);
  });
}
