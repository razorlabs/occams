/**
 *
 */
function StudyForm(data){
  data = data || {};

  var self = this;

  self.isNew = ko.observable();

  self.schema = ko.observable();
  self.versions = ko.observableArray();

  // Short-hand name getter
  self.name = ko.computed(function(){
    return self.schema() && self.schema().name;
  });

  // Short-hand title getter
  self.title = ko.computed(function(){
    return self.schema() && self.schema().title;
  });

  self.update = function(data){
    self.isNew(data.isNew || false);
    self.schema(data.schema || null);
    self.versions(data.versions || []);
  };

  self.hasMultipleVersions = ko.computed(function(){
    return self.versions().length > 1;
  });

  self.versionsLength = ko.computed(function(){
    return self.versions().length;
  });

  // Select2 schema search parameters callback
  self.searchSchemaParams = function(term, page){
    return {vocabulary: 'available_schemata', term: term};
  };

  // Select2 schema results callback
  self.searchSchemaResults = function(data){
    return {results: data.schemata};
  };

  // Select2 version search parameters callback
  self.searchVersionsParams = function(term, page){
    return {vocabulary: 'available_versions', schema: self.name(), term: term}
  };

  // Select2 version results callback
  self.searchVersionsResults = function(data){
    return {results: data.versions};
  };

  self.update(data);
}

/**
 * Cycle representation in the context of a study
 */
function StudyCycle(data){
  data = data || {};
  var self = this;

  self.__url__ = ko.observable();
  self.id = ko.observable();
  self.name = ko.observable();
  self.title = ko.observable();
  self.week = ko.observable();
  self.is_interim = ko.observable();
  self.forms = ko.observableArray();

  self.update = function(data){
    ko.mapping.fromJS(data, {
      'forms': {
        create: function(options){
          return new StudyForm(options.data);
        }
      }
    }, self);
  };

  self.hasForms = ko.computed(function(){
    return self.forms().length;
  });

  self.formsIndex = ko.computed(function(){
    var set = {};
    self.forms().forEach(function(form){
      set[form.schema().name] = true
    });
    return set;
  });

  self.containsForm = function(form){
    return form.schema().name in self.formsIndex();
  };

  self.update(data);
}

function StudyView(){
  var self = this;

  self.isReady = ko.observable(false);      // Indicates UI is ready
  self.isSaving = ko.observable(false);     // Indicates AJAX call

  self.isGridEnabled = ko.observable(false);// Grid disable/enable flag

  self.errorMessages = ko.observableArray([]);
  self.hasErrorMessages = ko.computed(function(){
    return self.errorMessages().length > 0;
  });

  // Modal states
  var VIEW = 'view', EDIT = 'edit',  DELETE = 'delete';

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

  self.study = ko.mapping.fromJSON($('#study-data').text(), {
    'termination_form': {
      create: function(options){
        return new StudyForm(options.data);
      }
    },
    'randomization_form': {
      create: function(options){
        return new StudyForm(options.data);
      }
    },
    'forms': {
      create: function(options){
        return new StudyForm(options.data);
      }
    },
    'cycles': {
      create: function(options){
        return new StudyCycle(options.data);
      }
    }
  });

  var byTitle = function(a, b){
    return a.title().localeCompare(b.title());
  };

  var byWeek = function(a, b){
    a = parseInt(ko.unwrap(a.week));
    b = parseInt(ko.unwrap(b.week));
    if (!isNaN(a) && isNaN(b)){
      return -1;
    } else if (isNaN(a) && !isNaN(b)){
      return 1;
    } else {
      return a - b;
    }
  };

  self.study.forms.sort(byTitle);
  self.study.cycles.sort(byWeek);

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

  /**
   * Re-usable error handler for XHR requests
   */
  var handleXHRError = function(form){
    return function(jqXHR, textStatus, errorThrown){
      if (textStatus.indexOf('CSRF') > -1 ){
        self.errorMessages(['You session has expired, please reload the page']);
      } else if (jqXHR.responseJSON){
        self.errorMessages(['Validation problems']);
        console.log(jqXHR.responseJSON.errors);
        $(form).validate().showErrors(jqXHR.responseJSON.errors);
      } else {
        self.errorMessages([errorThrown]);
      }
    };
  };

  self.saveCycle = function(form){
    if (!$(form).validate().form()){
      return;
    }

    var selected = self.selectedCycle();

    $.ajax({
      url: selected.id() ? selected.__url__() : $(form).data('factory-url'),
      type: selected.id() ? 'PUT' : 'POST',
      contentType: 'application/json; charset=utf-8',
      headers: {'X-CSRF-Token': $.cookie('csrf_token')},
      data: ko.toJSON(self.editableCycle()),
      beforeSend: function(){
        self.isSaving(true);
      },
      error: handleXHRError(form),
      success: function(data, textStatus, jqXHR){
        if (selected.id()){
          selected.update(data);
        } else {
          self.study.cycles.push(new StudyCycle(data));
        }
        self.study.cycles.sort(byWeek);
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
      error: handleXHRError(form),
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
      error: handleXHRError(form),
      success: function(data, textStatus, jqXHR){
        if (!selected.isNew()){
          selected.update(data);
        } else {
          self.study.forms.push(new StudyForm(data));
        }
        self.study.forms.sort(byTitle);
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
  };

  self.clear = function(){
    self.errorMessages([]);
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

  self.toggleGrid = function(data, event){
    console.log(event);
  };

  self.onCycleHover = function(data, event){
    console.log('adfdasf');
  }

  self.isReady(true);
}

+function($){
  "use strict";

  $(document).ready(function(){

    var element = $('#study-main')[0];

    if (!element){
      return;
    }

    ko.applyBindings(new StudyView(), element);

    /*
     * Scroll the grid
     */
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
  });

}(jQuery);
