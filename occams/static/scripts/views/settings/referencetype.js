function ReferenceTypesManageView(referenceTypesUrl){
  'use strict';

  var self = this;

  self.isReady = ko.observable(false);
  self.isAjaxing = ko.observable(false);

  self.referenceTypes = ko.observableArray();

  self.hasReferenceTypes = ko.pureComputed(function(){
    return self.referenceTypes().length > 0;
  });

  self.sortReferenceTypes = function(){
    self.referenceTypes.sort(function(a, b){ return a.title().localeCompare(b.title()); });
  };

  self.errorMessage = ko.observable();

  var VIEW = 'view', EDIT = 'edit', DELETE = 'delete';

  self.selectedReferenceType = ko.observable();
  self.editableReferenceType = ko.observable();
  self.latestReferenceType = ko.observable();
  self.addMoreReferenceTypes = ko.observable(false);
  self.statusReferenceType = ko.observable();
  self.showEditReferenceType = ko.pureComputed(function(){ return self.statusReferenceType() == EDIT; });
  self.showDeleteReferenceType = ko.pureComputed(function(){ return self.statusReferenceType() == DELETE; });

  self.clear = function(){
    self.selectedReferenceType(null);
    self.editableReferenceType(null);
    self.latestReferenceType(null);
    self.addMoreReferenceTypes(false);
    self.statusReferenceType(null);
  };

  self.startAddReferenceType = function(){
    self.startEditReferenceType(new ReferenceType());
  };

  self.startEditReferenceType = function(reference_type){
    self.statusReferenceType(EDIT);
    self.selectedReferenceType(reference_type);
    self.editableReferenceType(new ReferenceType(ko.toJS(reference_type)));
  };

  self.startDeleteReferenceType = function(reference_type){
    self.statusReferenceType(DELETE)
    self.selectedReferenceType(reference_type);
  };

  self.saveReferenceType = function(element){
    if ($(element).validate().form()){
      var selected = self.selectedReferenceType(),
          isNew = selected.isNew();
      $.ajax({
        url: isNew ? referenceTypesUrl : selected.__url__(),
        method: isNew ? 'POST' : 'PUT',
        contentType: 'application/json; charset=utf-8',
        data: ko.toJSON(self.editableReferenceType()),
        headers: {'X-CSRF-Token': $.cookie('csrf_token')},
        error: handleXHRError({form: element, logger: self.errroMessage}),
        beforeSend: function(){
          self.isAjaxing(true);
        },
        success: function(data){
          if (isNew){
            var reference_type = new ReferenceType(data);
            self.referenceTypes.push(reference_type);
            self.latestReferenceType(reference_type);
          } else {
            selected.update(data);
          }

          self.sortReferenceTypes();

          if (self.addMoreReferenceTypes()){
            self.startAddReferenceType();
          } else {
            self.clear();
          }
        },
        complete: function(){
          self.isAjaxing(false);
        }
      });
    }
  };

  self.deleteReferenceType = function(element){
    var selected = self.selectedReferenceType();
    $.ajax({
      url: selected.__url__(),
      method: 'DELETE',
      headers: {'X-CSRF-Token': $.cookie('csrf_token')},
      error: handleXHRError({form: element, logger: self.errroMessage}),
      beforeSend: function(){
        self.isAjaxing(true);
      },
      success: function(data){
        self.referenceTypes.remove(selected);
        self.clear();
      },
      complete: function(){
        self.isAjaxing(false);
      }
    });
  };

  $.get(referenceTypesUrl, function(data){
    self.referenceTypes(data.reference_types.map(function(value){ return new ReferenceType(value); }));
    self.sortReferenceTypes();
    self.isReady(true);
  });
}
