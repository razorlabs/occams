function StudyView(studyData, scheduleUrl){
  'use strict';

  var self = this;

  self.isReady = ko.observable(false);      // Indicates UI is ready
  self.isSaving = ko.observable(false);     // Indicates AJAX call
  self.isUploading = ko.observable(false);

  self.isGridEnabled = ko.observable(false);// Grid disable/enable flag

  self.successMessage = ko.observable();
  self.errorMessage = ko.observable();

  // Modal states
  var VIEW = 'view', EDIT = 'edit',  DELETE = 'delete';

  self.showUploadRids = ko.observable(false);

  self.previousCycle = ko.observable();
  self.selectedCycle = ko.observable();
  self.editableCycle = ko.observable();
  self.addMoreCycles = ko.observable(false);
  self.cycleModalState = ko.observable();
  self.showViewCycle = ko.computed(function(){ return self.cycleModalState() === VIEW; });
  self.showEditCycle = ko.computed(function(){ return self.cycleModalState() === EDIT; });
  self.showDeleteCycle = ko.computed(function(){ return self.cycleModalState() === DELETE; });

  self.previousForm = ko.observable();
  self.selectedForm = ko.observable();
  self.editableForm = ko.observable();
  self.addMoreForms = ko.observable(false);
  self.formModalState = ko.observable();
  self.showViewForm = ko.computed(function(){ return self.formModalState() === VIEW; });
  self.showEditForm = ko.computed(function(){ return self.formModalState() === EDIT; });
  self.showDeleteForm = ko.computed(function(){ return self.formModalState() === DELETE; });

  self.study = studyData ? new Study(studyData) : null;

  self.selectedStudy = ko.observable();
  self.editableStudy = ko.observable();
  self.previousStudy = ko.observable();
  self.studyModalState = ko.observable();
  self.showEditStudy = ko.computed(function(){ return self.studyModalState() === EDIT; });
  self.showDeleteStudy = ko.computed(function(){ return self.studyModalState() === DELETE; });

  self.startEditStudy = function(study, event){
    self.selectedStudy(study);
    self.editableStudy(new Study(ko.toJS(study)));
    self.studyModalState(EDIT);
  };

  self.startDeleteStudy = function(study, event){
    self.selectedStudy(study);
    self.studyModalState(DELETE);
  };

  self.startViewCycle = function(cycle, event){
    self.selectedCycle(cycle);
    self.cycleModalState(VIEW);
  };

  self.startAddCycle = function(){
    var cycle = new StudyCycle();
    self.selectedCycle(cycle);
    self.editableCycle(cycle);
    self.cycleModalState(EDIT);
  };

  self.startEditCycle = function(cycle, event){
    self.selectedCycle(cycle);
    self.editableCycle(new StudyCycle(ko.toJS(cycle)));
    self.cycleModalState(EDIT);
  };

  self.startDeleteCycle = function(cycle, event){
    self.selectedCycle(cycle);
    self.editableCycle(null);
    self.cycleModalState(DELETE);
  };

  self.startViewForm = function(form, event){
    self.selectedForm(form);
    self.formModalState(VIEW);
  };

  self.startAddForm = function(){
    var form = new StudyForm({isNew: true})
    self.selectedForm(form);
    self.editableForm(form);
    self.formModalState(EDIT);
  };

  self.startEditForm = function(form, event){
    self.selectedForm(form);
    self.editableForm(new StudyForm(ko.toJS(form)));
    self.formModalState(EDIT);
  };

  self.startDeleteForm = function(form, event){
    self.selectedForm(form);
    self.editableForm(null);
    self.formModalState(DELETE);
  };

  self.startUploadRids = function(){
    self.showUploadRids(true);
    $('<input type="file" />').on('change', function(event){
        var upload = new FormData();
        upload.append('upload', event.target.files[0]);

        // Clear error messages for next round of status updates
        self.errorMessage(null);

        $.ajax({
          url: window.location,
          type: 'POST',
          data: upload,
          headers: {'X-CSRF-Token': $.cookie('csrf_token')},
          processData: false,  // tell jQuery not to process the data
          contentType: false,  // tell jQuery not to set contentType
          error: handleXHRError({logger: self.errorMessage}),
          beforeSend: function(){
            self.isUploading(true);
          },
          success: function(data, textStatus, jqXHR){
            self.clear();
            self.successMessage('Successfully uploaded');
          },
          complete: function(jqXHR, textStatus){
            $(event.target).remove();
            self.isUploading(false);
          }
        });
    }).click();
  };

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
        }
        self.clear();
      },
      complete: function(){
        self.isSaving(false);
      }
    });
  };

  self.deleteStudy = function(form){
    var selected = self.selectedStudy();

    $.ajax({
      url: selected.__url__(),
      type: 'DELETE',
      contentType: 'application/json; charset=utf-8',
      headers: {'X-CSRF-Token': $.cookie('csrf_token')},
      beforeSend: function(){
        self.isSaving(true);
      },
      error: handleXHRError({logger: self.errorMessage, form: form}),
      success: function(data, textStatus, jqXHR){
        window.location = data.__next__
      },
      complete: function(){
        self.isSaving(false);
      }
    });
  };

  self.saveCycle = function(form){
    if (!$(form).validate().form()){
      return;
    }

    var selected = self.selectedCycle();

    $.ajax({
      url: selected.id() ? selected.__url__() : $(form).attr('action'),
      type: selected.id() ? 'PUT' : 'POST',
      contentType: 'application/json; charset=utf-8',
      headers: {'X-CSRF-Token': $.cookie('csrf_token')},
      data: ko.toJSON(self.editableCycle()),
      beforeSend: function(){
        self.isSaving(true);
      },
      error: handleXHRError({logger: self.errroMessage, form: form}),
      success: function(data, textStatus, jqXHR){
        if (selected.id()){
          selected.update(data);
        } else {
          self.study.cycles.push(new StudyCycle(data));
        }
        if (self.addMoreCycles()){
          self.previousCycle(selected);
          self.startAddCycle();
        } else {
          self.clear();
        }
      },
      complete: function(){
        self.isSaving(false);
      }
    });
  };

  self.deleteCycle = function(form){
    var selected = self.selectedCycle();
    $.ajax({
      url: selected.__url__(),
      type: 'DELETE',
      contentType: 'application/json; charset=utf-8',
      headers: {'X-CSRF-Token': $.cookie('csrf_token')},
      beforeSend: function(){
        self.isSaving(true);
      },
      error: handleXHRError({logger: self.errorMessage, form: form}),
      success: function(data, textStatus, jqXHR){
        self.study.cycles.remove(function(cycle){
          return selected.id() == cycle.id();
        });
        self.clear();
      },
      complete: function(){
        self.isSaving(false);
      }
    });
  };

  self.saveForm = function(form){
    if (!$(form).validate().form()){
      return;
    }

    var selected = self.selectedForm();

    $.ajax({
      url: $(form).attr('action'),
      type: 'POST',
      contentType: 'application/json; charset=utf-8',
      headers: {'X-CSRF-Token': $.cookie('csrf_token')},
      data: ko.toJSON({
        schema: self.editableForm().schema().name,
        versions: self.editableForm().versions().map(function(version){
          return version.id;
        })
      }),
      beforeSend: function(){
        self.isSaving(true);
      },
      error: handleXHRError({logger: self.errorMessage, form: form}),
      success: function(data, textStatus, jqXHR){
        if (!selected.isNew()){
          selected.update(data);
        } else {
          self.study.forms.push(new StudyForm(data));
        }
        if (self.addMoreForms()){
          self.previousForm(selected);
          self.startAddForm();
        } else {
          self.clear();
        }
      },
      complete: function(){
        self.isSaving(false);
      }
    });
  };

  self.deleteForm = function(form){
    var selected = self.selectedForm();
    $.ajax({
      // Shortcut to get this working
      // It's currently difficult to generate a URL for a form
      url: $(form).attr('action') + '/' + selected.name(),
      type: 'DELETE',
      headers: {'X-CSRF-Token': $.cookie('csrf_token')},
      contentType: 'application/json; charset=utf-8',
      beforeSend: function(){
        self.isSaving(true);
      },
      error: handleXHRError({logger: self.errorMessage, form: form}),
      success: function(data, textStatus, jqXHR){
        self.study.forms.remove(function(form){
          return selected.name() == form.name();
        });
        self.clear();
      },
      complete: function(){
        self.isSaving(false);
      }
    });
  };

  self.toggleForm  = function(cycle, form, event){

    if (!self.isGridEnabled()){
      return;
    }

    var enabled = !cycle.containsForm(form)
      , formName = form.name()
      , cycleId = cycle.id();

    $.ajax({
      url: scheduleUrl,
      type: 'PUT',
      headers: {'X-CSRF-Token': $.cookie('csrf_token')},
      contentType: 'application/json; charset=utf-8',
      data: ko.toJSON({cycle: cycleId, schema: formName, enabled: enabled}),
      beforeSend: function(){
        self.isSaving(true);
      },
      error: handleXHRError({logger: self.errorMessage}),
      success: function(data, textStatus, jqXHR){
        if (enabled){
          cycle.forms.push(form);
        } else {
          cycle.forms.remove(function(form){
            return form.name() == formName;
          });
        }
      },
      complete: function(){
        self.isSaving(false);
      }
    });
  };

  self.clear = function(){
    self.errorMessage();
    self.studyModalState(null)
    self.editableStudy(null);
    self.addMoreCycles(false);
    self.previousCycle(null);
    self.selectedCycle(null);
    self.editableCycle(null);
    self.cycleModalState(null);
    self.previousForm(null);
    self.selectedForm(null);
    self.editableForm(null);
    self.formModalState(null);
  };

  self.isReady(true);
}

function setupScheduleGrid(){
  // Scroll the grid
  function updateGrid(){
    var $container = $('#js-schedule')
      , $corner = $('#js-schedule-corner')
      , $header = $('#js-schedule-header')
      , $sidebar = $('#js-schedule-sidebar')
      // get scroll info relative to container
      , scrollTop = $(window).scrollTop() - $container.offset().top
      , scrollLeft = $container.scrollLeft()
      , affixLeft = 0 < scrollLeft
      , affixTop = 0 < scrollTop
        // (uncontrollable FF border)
      , headerHeight = $('#js-schedule-table thead th').outerHeight() - (affixTop ? 0 : 1)
      , headerWidth = $('#js-schedule-table thead th').outerWidth();

    if (affixTop){
      // affix header to the top side, allowing horizontal scroll
      $header.css({top: scrollTop}).show();
    } else {
      $header.hide();
    }

    if (affixLeft){
      // affix sidebar to left side under header, allowing vertical scroll
      $sidebar.css({top: headerHeight, left: scrollLeft}).show();
    } else {
      $sidebar.hide();
    }

    if (affixLeft || affixTop){
      // affix cornter to top left while scrolling
      $corner.find('th:first').css({height: headerHeight, width: headerWidth});
      $corner.css({top: affixTop ?  scrollTop : 0, left: affixLeft ? scrollLeft : 0}).show();
    } else {
      $corner.hide();
    }
  }

  $(window).on('scroll mousewheel resize', updateGrid);
  $('#js-schedule').on('scroll mousewheel', updateGrid);
}
