function PatientView(data){
  var self = this;

  self.isReady = ko.observable(false);
  self.isSaving = ko.observable(false);

  self.selected = ko.observable();
  self.editable = ko.observable();

  self.showEditForm = ko.observable();
  self.showDeleteForm = ko.observable()

  self.latestEnrollment = ko.observable();
  self.showEnrollmentEditForm = ko.observable(false);
  self.showRandomizationForm = ko.observable(false);
  self.showTerminationForm = ko.observable(false);

  self.latestVisit = ko.observable();
  self.showVisitEditForm = ko.observable(false);

  self.patient = ko.observable(new Patient(data.patient));

  self.clearSelected = function(){
    self.selected(null);
    self.editable(null);
    self.showEditForm(false);
    self.showDeleteForm(false);
    self.showVisitEditForm(false);
    self.showEnrollmentEditForm(false);
    self.showRandomizationForm(false);
    self.showTerminationForm(false);
  };

  self.doArchive = function(){
  };

  self.startEdit = function(){
    self.clearSelected();
    self.showEditForm(true);
    self.editable(new Patient(ko.mapping.toJS(self.patient())));
  }

  self.startDelete = function(){
    self.clearSelected();
    self.showDeleteForm(true);
    self.selected(self.patient);
  }

  self.startAddEnrollment = function(){
    self.clearSelected();
    self.showEnrollmentEditForm(true);
    self.editable(new Enrollment());
  }

  self.doEdit = function(element){
    self.isSaving(true);

    if (!$(element).validate().form()){
      return;
    }

    $.ajax({
      url: self.patient.__src__,
      method: 'PUT',
      contentType: 'application/json; charset=utf-8',
      data: ko.mapping.toJSON(self.editable()),
      headers: {'X-CSRF-Token': $.cookie('csrf_token')},
      error: function(jqXHR, textStatus, errorThrown){
        console.log('An error occurred, need to show something...');
        console.log(jqXHR.responseJSON);
      },
      success: function(data, textStatus, jqXHR){
        console.log(data);
        self.patient().update(data);
        self.clearSelected();
      },
      complete: function(){
        self.isSaving(false);
      }
    });
  };

  self.doEnroll = function(){
  };

  self.doRanzomize = function(){
  };

  self.doTerminate = function(){
  };

  self.isReady(true);
}

+function($){
  $(document).ready(function(){
    var $view = $('#patient');
    if ($view.length > 0){

      Site.availableOptions($.map(
        JSON.parse($('#availableSites-data').text()),
        function(data){ return new Site(data); }));

      // Configure Reference model to use only these reference types
      ReferenceType.availableOptions($.map(
        JSON.parse($('#availableReferenceTypes-data').text()),
        function(data){
          return new ReferenceType(data);
        }));

      ko.applyBindings(new PatientView({
        patient: JSON.parse($('#patient-data').text()),
        enrollments: JSON.parse($('#enrollments-data').text()),
        visits: JSON.parse($('#visits-data').text()),
      }), $view[0]);
    }
  });
}(jQuery);
