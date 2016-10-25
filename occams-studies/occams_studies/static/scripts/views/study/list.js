function StudyListingView(studiesData){
  'use strict';

  var self = this;

  self.isReady = ko.observable(false);
  self.isSaving = ko.observable(false);

  self.errorMessage = ko.observable();

  self.studies = ko.observableArray((studiesData || []).map(function(data){
    return new Study(data);
  }));

  self.studies.sort(function(a, b){
    return a.title().localeCompare(b.title());
  });

  self.hasStudies = ko.pureComputed(function(){
    return self.studies().length > 0;
  });

  self.selectedStudy = ko.observable();
  self.editableStudy = ko.observable();
  self.previousStudy = ko.observable();
  self.addMoreStudies = ko.observable(false);

  self.clear = function(){
    self.selectedStudy(null);
    self.editableStudy(null);
    self.errorMessage(null);
  };

  self.startAddStudy = function(){
    var study = new Study();
    self.selectedStudy(study);
    self.editableStudy(study);
  }

  // Note: this is the almost like the single study view's save,
  // but it needs to account for a listing of studies
  self.saveStudy = function(form){
    if (!$(form).validate().form()){
      return;
    }
    var selected = self.selectedStudy()
      , edits = ko.toJS(self.editableStudy());

    $.extend(edits, {
        // Convert to ids since this is what he REST API expects
        termination_form: edits.termination_form && edits.termination_form.versions[0].id,
        randomization_form: edits.randomization_form && edits.randomization_form.versions[0].id,
      });

    $.ajax({
      url: selected.id() ? selected.__url__() : $(form).attr('action'),
      type: selected.id() ? 'PUT' : 'POST',
      contentType: 'application/json; charset=utf-8',
      headers: {'X-CSRF-Token': $.cookie('csrf_token')},
      data: ko.toJSON(edits),
      beforeSend: function(){
        self.isSaving(true);
      },
      error: handleXHRError({logger: self.errorMessage, form: form}),
      success: function(data, textStatus, jqXHR){
        if (selected.id()){
          selected.update(data);
        } else {
          var study = new Study(data);
          self.previousStudy(study);
          self.studies.push(study);
        }

        self.studies.sort(function(a, b){
          return a.title().localeCompare(b.title());
        });

        if (self.addMoreStudies()){
          self.startAddStudy();
        } else {
          window.location = study.__url__();
        }
      },
      complete: function(){
        self.isSaving(false);
      }
    });
  };

  self.isReady(true);
};
