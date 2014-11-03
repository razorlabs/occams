function PatientView(){
  var self = this;

  self.isReady = ko.observable(false);
  self.isSaving = ko.observable(false);

  self.selectedItem = ko.observable();  // originally selected item
  self.editableItem = ko.observable();  // pending changes (will be applied to selected)

  var VIEW = 'view', EDIT = 'edit', DELETE = 'delete';

  // Patient UI settings
  self.statusPatient = ko.observable();
  self.showEditPatient = ko.pureComputed(function(){ return self.statusPatient() == EDIT });
  self.showDeletePatient = ko.pureComputed(function(){ return self.statusPatient() == DELETE });

  // Enrollment UI settings
  self.latestEnrollment = ko.observable();
  self.statusEnrollment = ko.observable();
  self.showEditEnrollment = ko.pureComputed(function(){ return self.statusEnrollment() == EDIT; });
  self.showDeleteEnrollment = ko.pureComputed(function(){ return self.statusEnrollment() == DELETE; });

  // Visti UI Settings
  self.latestVisit = ko.observable();
  self.statusVisit = ko.observable();
  self.showEditVisit = ko.pureComputed(function(){ return self.statusVisit() == EDIT; });

  // Modal UI Settings
  self.errorMessage = ko.observable();

  // UI Data
  self.patient = new Patient(JSON.parse($('#patient-data').text()));
  self.enrollments = ko.mapping.fromJSON($('#enrollments-data').text());
  self.visits = ko.observableArray(JSON.parse($('#visits-data').text()).map(function(data){
    return new Visit(data);
  }));

  self.hasEnrollments = ko.computed(function(){
    return self.enrollments().length > 0;
  });

  self.hasVisits = ko.computed(function(){
    return self.visits().length > 0;
  });

  self.select2ParamsSite = function(term,  page){
    return {vocabulary: 'available_sites', term: term};
  };

  self.select2ResultsSite = function(data, page, query){
    return {
      results: data.sites.map(function(value){
        return new Site(value);
      })
    };
  };

  self.select2ParamsReferenceType = function(term, page){
    return {vocabulary: 'available_reference_types', term: term};
  };

  self.select2ResultsReferenceType = function(data, page, query){
    return {
      results: data.reference_types.map(function(value){
        return new ReferenceType(value);
      })
    };
  };

  self.onChangeStudy = function(item, event){
    var $option = $($(event.target).find(':selected'))
      , $field = $('#reference_number')
      , pattern = $option.data('reference_pattern')
      , hint = $option.data('reference_hint');

    if (pattern){
      $field.attr('pattern', pattern);
    } else {
      $field.removeAttr('pattern');
    }

    if (hint){
      $field.attr('placeholder', hint);
    } else {
      $field.removeAttr('placeholder');
    }
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
  };

  self.startEditPatient = function(){
    self.clear();
    self.statusPatient(EDIT);
    self.editableItem(new Patient(self.patient.toJS()));
  };

  self.startDeletePatient = function(){
    self.clear();
    self.statusPatient(DELETE);
  };

  self.startAddEnrollment = function(){
    self.clear();
    self.statusEnrollment(EDIT);
    self.editableItem({
      // make a copy for editing
      id: ko.observable(),
      study: ko.observable(),
      consent_date: ko.observable(),
      latest_consent_date: ko.observable(),
      reference_number: ko.observable(),
    });
  };

  self.startEditEnrollment = function(item){
    self.clear();
    self.statusEnrollment(EDIT);
    self.selectedItem(item)
    self.editableItem({
      // make a copy for editing
      id: ko.observable(item.id()),
      study: ko.observable(item.study.id()),
      consent_date: ko.observable(item.consent_date()),
      latest_consent_date: ko.observable(item.latest_consent_date()),
      reference_number: ko.observable(item.reference_number()),
    });
  };

  self.startDeleteEnrollment = function(item){
    self.clear();
    self.showDeleteEnrollment(true);
    self.selectedItem(item)
  };

  self.startAddVisit = function(){
    self.clear();
    self.statusVisit(EDIT);
    self.editableItem({
      id: ko.observable(),
      cycles: ko.observableArray([]),
      visit_date: ko.observable(),
      include_forms: ko.observable(),
      include_speciemen: ko.observable()
    });
  };

  self.visitSelect2Options = function(element){
    return {
      multiple: true,
      ajax: {
        url: $(element).data('cycles-url'),
        quietMillis: 100,
        minimumInputLength: 3,
        data: function (term, page) {
          return {q: term};
        },
        results: function (data) {
          return {
            results: $.map(data.cycles, function (item) {
              return {
                text: item.title,
                id: item.id
              }
            })
          };
        },
      }
    }
  };

  self.savePatient = function(element){
    if ($(element).validate().form()){
      $.ajax({
        url: self.patient.__src__,
        method: 'PUT',
        contentType: 'application/json; charset=utf-8',
        data: ko.mapping.toJSON(self.editableItem()),
        headers: {'X-CSRF-Token': $.cookie('csrf_token')},
        error: handleXHRError({form: element, logger: self.errorMessage}),
        beforeSend: function(){
          self.isSaving(true);
        },
        success: function(data, textStatus, jqXHR){
          ko.mapping.fromJS(data, {}, self.patient);
          self.clear();
        },
        complete: function(){
          self.isSaving(false);
        }
      });
    }
  };

  self.deletePatient = function(element){
    $.ajax({
      url: self.patient.__src__,
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
        data: ko.mapping.toJSON(self.editableItem()),
        headers: {'X-CSRF-Token': $.cookie('csrf_token')},
        error: handleXHRError({form: element, logger: self.errorMessage}),
        beforeSend: function(){
          self.isSaving(true);
        },
        success: function(data, textStatus, jqXHR){
          if (selected.id()){
            ko.mapping.fromJS(data, {}, selected)
          } else {
            self.enrollments.push(ko.mapping.fromJS(data));
          }
          self.enrollments.sort(function(left, right){
            return left.consent_date() > right.consent_date() ? -1 : 1;
          });
          self.clear();
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
        data: ko.mapping.toJSON(self.editableItem()),
        headers: {'X-CSRF-Token': $.cookie('csrf_token')},
        error: handleXHRError({form: element, logger: self.errorMessage}),
        beforeSend: function(){
          self.isSaving(true);
        },
        success: function(data, textStatus, jqXHR){
          self.visits.push(ko.mapping.fromJS(data));
          self.clear();
        },
        complete: function(){
          self.isSaving(false);
        }
      });
    }
  };

  // Object initalized, set flag to display main UI
  self.isReady(true);
}
