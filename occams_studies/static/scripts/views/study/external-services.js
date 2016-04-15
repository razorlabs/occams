/**
 * Manages the listing of external services for a study
 */
function ExternalServicesView(options){
  'use strict'

  var self = this;

  self.isReady = ko.observable(false);      // Indicates UI is ready
  self.isSaving = ko.observable(false);     // Indicates AJAX call

  self.externalServices = ko.observableArray();

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

  /**
   * Resets the UI
   */
  self.clear = function(){
    self.mode(null);
    self.selectedService(null);
    self.editableService(null);
  };

  // Keeps the list of external services sorted
  self.sortExternalServices = function(){
    self.externalServices.sort(function(a, b){ return a.title().localeCompare(b.title()); });
  };

  /**
   * Sets the UI to EDIT mode with a brand new service
   */
  self.startAddExternalService = function(){
    self.selectedService(new ExternalService());
    self.editableService(new ExternalService());
    self.mode(EDIT);
  };

  /**
   * Sets the UI to EDIT mode with an existing service
   */
  self.startEditExternalService = function(service){
    self.selectedService(service);
    self.editableService(new ExternalService(ko.toJS(service)));
    self.mode(EDIT);
  };

  /**
   * Validates and sends all changes to the REST API endpoint
   */
  self.saveService = function(element){
    if (!$(element).validate().form()){
      return;
    }

    var selected = self.selectedService(),
        editable = self.editableService();

    $.ajax({
      url: selected.isNew() ? options.serviceUrl : selected.__url__(),
      method: selected.isNew() ? 'POST' : 'PUT',
      contentType: 'application/json; charset=utf-8',
      data: ko.toJSON(editable),
      headers: {'X-CSRF-Token': $.cookie('csrf_token')},
      error: handleXHRError({form: element, logger: self.errorMessage}),
      beforeSend: function(){
        self.isSaving(true);
      },
      success: function(data){
        if (selected.isNew()){
          self.externalServices.push(new ExternalService(data));
        } else {
          selected.update(data);
        }
        self.sortExternalServices();
        self.clear();
      },
      complete: function(){
        self.isSaving(false);
      }
    });
  };

  /**
   * Sets the UI to DELETE mode with an existing service
   */
  self.startDeleteExternalService = function(service){
    self.selectedService(service);
    self.mode(DELETE);
  };

  /**
   * Sends a DELETE request to the REST API endpoint
   */
  self.deleteService = function(element){
    var selected = self.selectedService();
    $.ajax({
      url: selected.__url__(),
      method: 'DELETE',
      headers: {'X-CSRF-Token': $.cookie('csrf_token')},
      error: handleXHRError({form: element, logger: self.errorMessage}),
      beforeSend: function(){
        self.isSaving(true);
      },
      success: function(data){
        self.externalServices.remove(selected);
        self.clear();
      },
      complete: function(){
        self.isSaving(false);
      }
    });
  };

  // Loads initial data on ojects-instantiation
  $.getJSON(options.serviceUrl, function(data){
    self.externalServices(data.external_services.map(function(rawData){
      return new ExternalService(rawData)
    }));

    self.isReady(true);
  });
}
