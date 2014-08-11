function PatientView(data){
  var self = this;

  self.isReady = ko.observable(false);

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

  self.patient = ko.observable(new Patient(data));

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
    self.selected(self.patient());
    self.editable(new Patient(self.patient().toJS()));
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

  self.doEdit = function(){
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
      var data = JSON.parse($('#data').text());
      ko.applyBindings(new PatientView(data), $view[0]);
    }
  });
}(jQuery);
