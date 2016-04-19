function PatientView(options){
  'use strict';

  options = options || {};

  var self = this;

  self.isReady = ko.observable(false);
  self.isSaving = ko.observable(false);

  self.selectedItem = ko.observable();  // originally selected item
  self.editableItem = ko.observable();  // pending changes (will be applied to selected)

  var VIEW = 'view', ADD = 'add', EDIT = 'edit', DELETE = 'delete', TERMINATE = 'terminate', RANDOMIZE = 'randomize';

  // Patient UI settings
  self.statusPatient = ko.observable();
  self.showEditPatient = ko.pureComputed(function(){ return self.statusPatient() == EDIT });
  self.showDeletePatient = ko.pureComputed(function(){ return self.statusPatient() == DELETE });

  // Enrollment UI settings
  self.latestEnrollment = ko.observable();
  self.statusEnrollment = ko.observable();
  self.showEditEnrollment = ko.pureComputed(function(){ return self.statusEnrollment() == EDIT; });
  self.showDeleteEnrollment = ko.pureComputed(function(){ return self.statusEnrollment() == DELETE; });
  self.showRandomizeEnrollment = ko.pureComputed(function(){ return self.statusEnrollment() == RANDOMIZE; });
  self.showTerminateEnrollment = ko.pureComputed(function(){ return self.statusEnrollment() == TERMINATE; });

  // Visit UI Settings
  self.latestVisit = ko.observable();
  self.statusVisit = ko.observable();
  self.showEditVisit = ko.pureComputed(function(){ return self.statusVisit() == EDIT; });

  // Forms UI settings
  self.entities = ko.observableArray((options.entitiesData || []).map(function(value){ return new Entity(value); } ));
  self.statusForm = ko.observable();
  self.showAddForm = ko.pureComputed(function(){ return self.statusForm() == ADD; });
  self.showDeleteForm = ko.pureComputed(function(){ return self.statusForm() == DELETE; });
  self.isAllSelected = ko.observable(false);

  self.selectAll = function(){
    var all = this.isAllSelected();
    self.entities().forEach(function(entity) {
      entity.isSelected(!all);
    });
    return true;
  };

  self.hasSelectedForms = ko.pureComputed(function(){
    return self.entities().some(function(entity){ return entity.isSelected(); });
  });

  // Modal UI Settings
  self.errorMessage = ko.observable();

  // UI Data
  self.patient = new Patient(options.patientData);

  self.enrollments = ko.observableArray((options.enrollmentsData || []).map(function(value){
    return new Enrollment(value);
  }));

  self.visits = ko.observableArray((options.visitsData || []).map(function(value){
    return new Visit(value);
  }));

  self.hasEnrollments = ko.pureComputed(function(){
    return self.enrollments().length > 0;
  });

  self.hasVisits = ko.pureComputed(function(){
    return self.visits().length > 0;
  });

  /**
   * Select2 Parameters for loading available studies via AJAX
   */
  self.select2StudyOptions = function(){
    return {
      allowClear: true,
      ajax: {
        data: function(term, page){
          return {vocabulary: 'available_studies', term: term};
        },
        results: function(data){
          return {
            results: data.studies.map(function(value){
              return new Study(value);
            })
          };
        }
      }
    };
  };

  /**
   * Clears all UI settings
   */
  self.clear = function(){
    self.errorMessage(null);
    self.selectedItem(null);
    self.editableItem(null);
    self.statusPatient(null);
    self.statusEnrollment(null);
    self.statusVisit(null);
    self.statusForm(null);
  };

  self.startAddPatient = function(){
    self.clear();
    self.statusPatient(EDIT);
    self.editableItem(new Patient());
  };

  self.startEditPatient = function(){
    self.clear();
    self.statusPatient(EDIT);
    self.editableItem(new Patient(ko.toJS(self.patient)));
  };

  self.startDeletePatient = function(){
    self.clear();
    self.statusPatient(DELETE);
  };

  self.startAddEnrollment = function(){
    self.clear();
    self.startEditEnrollment(new Enrollment());
  };

  self.startEditEnrollment = function(item){
    self.clear();
    self.statusEnrollment(EDIT);
    self.selectedItem(item)
    self.editableItem(new Enrollment(ko.toJS(item)));
  };

  self.startDeleteEnrollment = function(item){
    self.clear();
    self.statusEnrollment(DELETE);
    self.selectedItem(item)
  };

  self.startTerminateEnrollment = function(item){
    self.clear();
    $.get(item.__termination_url__(), function(data, textSatus, jqXHR){
      self.statusEnrollment(TERMINATE);
      self.selectedItem(item);
      var editable = new Enrollment(ko.toJS(item))
      editable.termination_ui(data);
      self.editableItem(editable);
    });
  };

  self.startRandomizeEnrollment = function(item){
    self.clear();
    $.get(item.__randomization_url__(), function(data, textSatus, jqXHR){
      self.statusEnrollment(RANDOMIZE);
      self.selectedItem(item);
      var editable = new Enrollment(ko.toJS(item))
      editable.randomization_ui(data.content)
      self.editableItem(editable);
    });
  };

  self.startAddVisit = function(){
    self.clear();
    self.statusVisit(EDIT);
    self.editableItem(new Visit());
  };

  self.startAddForm = function(){
    self.clear();
    self.statusForm(ADD);
    self.editableItem(new Entity());
  };

  self.startDeleteForms = function(){
    self.clear();
    self.statusForm(DELETE);
  };

  self.savePatient = function(element){
    if ($(element).validate().form()){
      var patient = self.patient,
          isNew = patient.isNew();

      $.ajax({
        url: isNew ? $(element).attr('action') : patient.__url__(),
        method: isNew ? 'POST' : 'PUT',
        contentType: 'application/json; charset=utf-8',
        data: ko.toJSON(self.editableItem().toRest()),
        headers: {'X-CSRF-Token': $.cookie('csrf_token')},
        error: handleXHRError({form: element, logger: self.errorMessage}),
        beforeSend: function(){
          self.isSaving(true);
        },
        success: function(data, textStatus, jqXHR){
          if (isNew){
            window.location = data.__url__
          } else {
            patient.update(data);
            self.clear();
          }
        },
        complete: function(){
          // Re-directing takes a while, keep the user in the modal if it's a record
          // Also, remove rotating icon if there were errors
          if (!isNew || self.errorMessage()){
            self.isSaving(false);
          }
        }
      });
    }
  };

  self.deletePatient = function(element){
    $.ajax({
      url: self.patient.__url__(),
      method: 'DELETE',
      headers: {'X-CSRF-Token': $.cookie('csrf_token')},
      error: handleXHRError({form: element, logger: self.errorMessage}),
      beforeSend: function(){
        self.isSaving(true);
      },
      success: function(data, textStatus, jqXHR){
        window.location = data.__next__;
      },
      complete: function(){
        self.isSaving(false);
      }
    });
  };

  self.saveEnrollment = function(element){
    if ($(element).validate().form()){
      var selected = self.selectedItem();

      $.ajax({
        url: selected.id() ? selected.__url__() : $(element).data('factory-url'),
        method: selected.id() ? 'PUT' : 'POST',
        contentType: 'application/json; charset=utf-8',
        data: ko.toJSON(self.editableItem().toRest()),
        headers: {'X-CSRF-Token': $.cookie('csrf_token')},
        error: handleXHRError({form: element, logger: self.errorMessage}),
        beforeSend: function(){
          self.isSaving(true);
        },
        success: function(data, textStatus, jqXHR){
          if (selected.id()){
            selected.update(data);
          } else {
            self.enrollments.push(new Enrollment(data));
          }
          self.enrollments.sort(function(left, right){
            return left.consent_date() > right.consent_date() ? -1 : 1;
          });

          $.getJSON(self.patient.__url__(), function(data){
              self.patient.update(data)
          });

          self.clear();
        },
        complete: function(){
          self.isSaving(false);
        }
      });
    }
  };

  self.terminateEnrollment = function(element){
    if ($(element).validate().form()){
      var item = self.selectedItem();
      $.ajax({
        url: item.__termination_url__(),
        method: 'POST',
        data: $(element).serialize(),
        headers: {'X-CSRF-Token': $.cookie('csrf_token')},
        error: handleXHRError({form: element, logger: self.errorMessage}),
        beforeSend: function(){
          self.isSaving(true);
        },
        success: function(data, textStatus, jqXHR){
          item.update(data);
          self.clear();
        },
        complete: function(){
          self.isSaving(false);
        }
      });
    }
  };

  self.randomizeEnrollment = function(element){
    if ($(element).validate().form()){
      var editable = self.editableItem();
      $.ajax({
        url: editable.__randomization_url__(),
        method: 'POST',
        data: $(element).serialize(),
        headers: {'X-CSRF-Token': $.cookie('csrf_token')},
        error: handleXHRError({form: element, logger: self.errorMessage}),
        beforeSend: function(){
          self.isSaving(true);
        },
        success: function(data, textStatus, jqXHR){
          if (data.is_randomized){
            var item = self.selectedItem();
            item.update(data.enrollment);
          } else {
            // Keep rendering the form until the enrollment is
            // randomized. The server will keep track of the process
            editable.randomization_ui(null);
          }
          editable.randomization_ui(data.content);
        },
        complete: function(){
          self.isSaving(false);
        }
      });
    }
  };

  self.deleteEnrollment = function(element){
    var item = self.selectedItem();

    $.ajax({
      url: item.__url__(),
      method: 'DELETE',
      headers: {'X-CSRF-Token': $.cookie('csrf_token')},
      error: handleXHRError({form: element, logger: self.errorMessage}),
      beforeSend: function(){
        self.isSaving(true);
      },
      success: function(data, textStatus, jqXHR){
        self.enrollments.remove(item);
        self.clear();
        $.getJSON(self.patient.__url__(), function(data){
            self.patient.update(data)
        });
      },
      complete: function(){
        self.isSaving(false);
      }
    });
  };

  self.saveVisit = function(element){
    if ($(element).validate().form()){
      $.ajax({
        url: $(element).attr('action'),
        method: 'POST',
        contentType: 'application/json; charset=utf-8',
        data: ko.toJSON(self.editableItem().toRest()),
        headers: {'X-CSRF-Token': $.cookie('csrf_token')},
        error: handleXHRError({form: element, logger: self.errorMessage}),
        beforeSend: function(){
          self.isSaving(true);
        },
        success: function(data, textStatus, jqXHR){
          self.visits.push(new Visit(data));
          self.visits.sort(function(a, b){ return -1 * a.visit_date().localeCompare(b.visit_date()); });
          self.clear();
        },
        complete: function(){
          self.isSaving(false);
        }
      });
    }
  };

  self.saveForm = function(element){
    if ($(element).validate().form()){
       $.ajax({
        url: $(element).attr('action'),
        method: 'POST',
        contentType: 'application/json; charset=utf-8',
        data: ko.toJSON(self.editableItem().toRest()),
        headers: {'X-CSRF-Token': $.cookie('csrf_token')},
        error: handleXHRError({form: element, logger: self.errorMessage}),
        beforeSend: function(){
          self.isSaving(true);
        },
        success: function(data, textStatus, jqXHR){
          window.location = data.__next__;
          self.clear();
        },
        complete: function(){
          self.isSaving(false);
        }
      });
    }
  };

  self.deleteForms = function(element){
    var entities = self.entities()
      , selected = entities.filter(function(e){ return e.isSelected(); })
      , ids = selected.map(function(e){ return e.id(); });

    $.ajax({
        url: options.formsUrl,
        method: 'DELETE',
        contentType: 'application/json; charset=utf-8',
        data: ko.toJSON({forms: ids}),
        headers: {'X-CSRF-Token': $.cookie('csrf_token')},
        error: handleXHRError({form: element, logger: self.errorMessage}),
        beforeSend: function(){
          self.isSaving(true);
        },
        success: function(data, textStatus, jqXHR){
          var not_selected = entities.filter(function(e){ return !e.isSelected(); });
          self.entities(not_selected);
          self.isAllSelected(false);
          self.clear();
        },
        complete: function(){
          self.isSaving(false);
        }
    });
  };

  // Object initalized, set flag to display main UI
  self.isReady(true);
}
