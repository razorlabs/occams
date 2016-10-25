function PatientFormsManageView(formsUrl){
  'use strict';

  var self = this;

  self.isReady = ko.observable(false);
  self.isAjaxing = ko.observable(false);

  self.forms = ko.observableArray();

  self.hasForms = ko.pureComputed(function(){
    return self.forms().length > 0;
  });

  self.sortForms = function(){
    self.forms.sort(function(a, b){ return a.title().localeCompare(b.title()); });
  };

  self.errorMessage = ko.observable();

  var VIEW = 'view', EDIT = 'edit', DELETE = 'delete';

  self.selectedForm = ko.observable();
  self.editableForm = ko.observable();
  self.latestForm = ko.observable();
  self.addMoreForms = ko.observable(false);

  self.statusForm = ko.observable();
  self.showEditForm = ko.pureComputed(function(){ return self.statusForm() == EDIT; });
  self.showDeleteForm = ko.pureComputed(function(){ return self.statusForm() == DELETE; });

  self.clear = function(){
    self.selectedForm(null);
    self.editableForm(null);
    self.latestForm(null);
    self.addMoreForms(false);
    self.statusForm(null);
  };

  // Select2 schema search parameters callback
  self.searchSchemaParams = function(term, page){
    return {vocabulary: 'available_schemata', term: term, grouped: true};
  };

  // Select2 schema results callback
  self.searchSchemaResults = function(data){
    return {
      results: data.schemata.map(function(value){
        return new StudyForm(value);
      })
    };
  };

  self.startAddForm = function(){
    self.startEditForm(new StudyForm());
  };

  self.startEditForm = function(form){
    self.statusForm(EDIT)
    self.selectedForm(form);
    self.editableForm(new StudyForm(ko.toJS(form)));
  };

  self.startDeleteForm = function(form){
    self.statusForm(DELETE)
    self.selectedForm(form);
  };

  self.saveForm = function(element){
    if ($(element).validate().form()){
      $.ajax({
        url: formsUrl,
        method: 'POST',
        contentType: 'application/json; charset=utf-8',
        data: ko.toJSON({form: self.editableForm().versions()[0].id}),
        headers: {'X-CSRF-Token': $.cookie('csrf_token')},
        error: handleXHRError({form: element, logger: self.errorMessage}),
        beforeSend: function(){
          self.isAjaxing(true);
        },
        success: function(data){
          self.forms.push(new StudyForm(data));
          self.sortForms()

          if (self.addMoreForms()){
            self.startAddSite();
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

  self.deleteForm = function(element){
    var selected = self.selectedForm();
    $.ajax({
      url: formsUrl,
      data: ko.toJSON({form: selected.versions()[0].id}),
      method: 'DELETE',
      headers: {'X-CSRF-Token': $.cookie('csrf_token')},
      error: handleXHRError({form: element, logger: self.errorMessage}),
      beforeSend: function(){
        self.isAjaxing(true);
      },
      success: function(data){
        self.forms.remove(selected);
        self.clear();
      },
      complete: function(){
        self.isAjaxing(false);
      }
    });
  };

  $.get(formsUrl, function(data){
    self.forms((data.forms || []).map(function(value){ return new StudyForm(value); }));
    self.sortForms();
    self.isReady(true);
  });
}
