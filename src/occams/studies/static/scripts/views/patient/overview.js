function PatientView(){
  var self = this;

  self.isReady = ko.observable(false);
  self.isSaving = ko.observable(false);

  self.selectedItem = ko.observable();  // originally selected item
  self.editableItem = ko.observable();  // pending changes (will be applied to selected)

  // Patient UI settings
  self.showEditForm = ko.observable(false);
  self.showDeleteForm = ko.observable(false)

  // Enrollment UI settings
  self.latestEnrollment = ko.observable();
  self.showEnrollmentForm = ko.observable(false);
  self.showEnrollmentDelete = ko.observable(false);

  // Visti UI Settings
  self.latestVisit = ko.observable();
  self.showVisitForm = ko.observable(false);
  self.showVisitDelete = ko.observable(false);

  // Modal UI Settings
  self.errorMessages = ko.observableArray();
  self.hasErrorMessages = ko.computed(function(){
      return self.errorMessages().length > 0;
  });

  // UI Data
  self.patient = ko.mapping.fromJSON($('#patient-data').text());
  self.enrollments = ko.mapping.fromJSON($('#enrollments-data').text());
  self.visits = ko.observableArray(ko.utils.arrayMap(JSON.parse($('#visits-data').text()), function(data){
    return new Visit(data);
  }));

  self.hasReferences = ko.computed(function(){
    return self.patient.references().length > 0;
  });

  self.hasEnrollments = ko.computed(function(){
    return self.enrollments().length > 0;
  });

  self.hasVisits = ko.computed(function(){
    return self.visits().length > 0;
  });

  self.onChangeReferenceType = function(item, event){
    var $option = $($(event.target).find(':selected'))
      , $field = $option.closest('.row').find('input.reference_number')
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
    self.selectedItem(null);
    self.editableItem(null);
    self.showEditForm(false);
    self.showDeleteForm(false);
    self.showEnrollmentForm(false);
    self.showEnrollmentDelete(false);
    self.showVisitForm(false);
    self.showVisitDelete(false);
    self.errorMessages([]);
  };

  self.startEdit = function(){
    self.clear();
    self.showEditForm(true);
    self.editableItem({
      // Make a copy for editing
      site: ko.observable(self.patient.site.id()),
      references: ko.observableArray($.map(self.patient.references(), function(r){
        return {
          reference_type: ko.observable(r.reference_type.id()),
          reference_number: ko.observable(r.reference_number())
        };
      }))
    });
  };

  self.deleteReference = function(reference){
    self.editableItem().references.remove(reference);
  }

  self.addReference = function(reference){
    self.editableItem().references.push({reference_type: null, reference_number: null});
  }

  /**
   * Re-usable error handler for XHR requests
   */
  var handleXHRError = function(jqXHR, textStatus, errorThrown){
    if (textStatus.indexOf('CSRF') > -1 ){
      self.errorMessages(['You session has expired, please reload the page']);
    } else if (jqXHR.responseJSON){
      self.errorMessages(jqXHR.responseJSON.validation_errors);
    } else {
      self.errorMessages([errorThrown]);
    }
  };

  self.startDelete = function(){
    self.clear();
    self.showDeleteForm(true);
  };

  self.startAddEnrollment = function(){
    self.clear();
    self.showEnrollmentForm(true);
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
    self.showEnrollmentForm(true);
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
    self.showEnrollmentDelete(true);
    self.selectedItem(item)
  };

  self.startAddVisit = function(){
    self.clear();
    self.showVisitForm(true);
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

    if (!$(element).validate().form()){
      return;
    }

    self.isSaving(true);

    $.ajax({
      url: self.patient.__src__,
      method: 'PUT',
      contentType: 'application/json; charset=utf-8',
      data: ko.mapping.toJSON(self.editableItem()),
      headers: {'X-CSRF-Token': $.cookie('csrf_token')},
      error: handleXHRError,
      success: function(data, textStatus, jqXHR){
        ko.mapping.fromJS(data, {}, self.patient);
        self.clear();
      },
      complete: function(){
        self.isSaving(false);
      }
    });
  };

  self.deletePatient = function(element){
    self.isSaving(true);
    $.ajax({
      url: self.patient.__src__,
      method: 'DELETE',
      headers: {'X-CSRF-Token': $.cookie('csrf_token')},
      error: handleXHRError,
      success: function(data, textStatus, jqXHR){
        window.location = data.__next__;
      },
      complete: function(){
        self.isSaving(false);
      }
    });
  };

  self.saveEnrollment = function(element){
    if (!$(element).validate().form()){
      return;
    }

    self.isSaving(true);

    var selected = self.selectedItem();

    $.ajax({
      url: selected.id() ? selected.__url__() : $(element).data('factory-url'),
      method: selected.id() ? 'PUT' : 'POST',
      contentType: 'application/json; charset=utf-8',
      data: ko.mapping.toJSON(self.editableItem()),
      headers: {'X-CSRF-Token': $.cookie('csrf_token')},
      error: handleXHRError,
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
  };

  self.deleteEnrollment = function(){
    self.isSaving(true);
    var item = self.selectedItem();

    $.ajax({
      url: item.__url__(),
      method: 'DELETE',
      headers: {'X-CSRF-Token': $.cookie('csrf_token')},
      error: handleXHRError,
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
    if (!$(element).validate().form()){
      return;
    }

    self.isSaving(true);
    console.log(ko.mapping.toJSON(self.editableItem()));

    $.ajax({
      url: $(element).attr('action'),
      method: 'POST',
      contentType: 'application/json; charset=utf-8',
      data: ko.mapping.toJSON(self.editableItem()),
      headers: {'X-CSRF-Token': $.cookie('csrf_token')},
      error: handleXHRError,
      success: function(data, textStatus, jqXHR){
        self.visits.push(ko.mapping.fromJS(data));
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
