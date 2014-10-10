/**
 * Schema representation in the context of a study
 */
function StudySchema(data){
  var self = this;
  self.name = data.name;
  self.title = data.title
  self.versions = ko.observableArray(data.versions);
  self.hasMultipleVersions = ko.computed(function(){
    return self.versions().length > 1;
  });
  self.versionsLength = ko.computed(function(){
    return self.versions().length;
  });
}

/**
 * Cycle representation in the context of a study
 */
function StudyCycle(data){
  var self = this;

  self.__url__ = ko.observable();
  self.id = ko.observable();
  self.name = ko.observable();
  self.title = ko.observable();
  self.week = ko.observable();
  self.is_interim = ko.observable();
  self.schemata = ko.observableArray();

  self.update = function(data){
    ko.mapping.fromJS(data, {
      'schemata': {
        create: function(options){
          return new StudySchema(options.data);
        }
      }
      }, self);
  };

  self.hasSchemata = ko.computed(function(){
    return self.schemata().length;
  });

  self.schemataIndex = ko.computed(function(){
    var set = {};
    self.schemata().forEach(function(schema){
      set[schema.name] = true
    });
    return set;
  });

  self.containsSchema = function(name){
    return name in self.schemataIndex();
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

  self.selectedCycle = ko.observable();
  self.editableCycle = ko.observable();
  self.cycleModalState = ko.observable();
  self.showViewCycle = ko.computed(function(){ return self.cycleModalState() === VIEW; });
  self.showEditCycle = ko.computed(function(){ return self.cycleModalState() === EDIT; });
  self.showDeleteCycle = ko.computed(function(){ return self.cycleModalState() === DELETE; });

  self.study = ko.mapping.fromJSON($('#study-data').text(), {
    'schemata': {
      create: function(options){
        return new StudySchema(options.data);
      }
    },
    'cycles': {
      create: function(options){
        return new StudyCycle(options.data);
      }
    }
  });

  self.startViewCycle = function(cycle, event){
    self.selectedCycle(cycle);
    self.cycleModalState(VIEW);
  };

  self.startEditCycle = function(cycle, event){
    self.selectedCycle(cycle);
    self.editableCycle(new StudyCycle(ko.mapping.toJS(cycle)));
    self.cycleModalState(EDIT);
  };

  self.startDeleteCycle = function(cycle, event){
    self.selectedCycle(cycle);
    self.editableCycle(null);
    self.cycleModalState(DELETE);
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
      data: ko.mapping.toJSON(self.editableCycle()),
      beforeSend: function(){
        self.isSaving(true);
      },
      error: handleXHRError(form),
      success: function(data, textStatus, jqXHR){
        if  (selected.id()){
          selected.update(data);
        } else {
          self.study.cycles.push(new StudyCycle(data));
        }
        self.study.cycles.sort(function(a, b){
          return a.title().localeCompare(b.title());
        });
        self.clear();
      },
      complete: function(){
        self.isSaving(false);
      }
    });
  };

  self.deleteCycle = function(cycle, event){
  };

  self.clear = function(){
    self.errorMessages([]);
    self.selectedCycle(null);
    self.editableCycle(null);
    self.cycleModalState(null);
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
  $(document).ready(function(){
    var $view = $('#view-study')[0];
    if (!$view){
      return;
    }

    ko.applyBindings(new StudyView(), $view);

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
        , headerHeight = $('#js-schedule-table thead').height()
        , sidebarWidth = $('#js-schedule-table tbody th:first').outerWidth()
        , affixLeft = 0 < scrollLeft
        , affixTop = 0 < scrollTop;

      if (affixTop){
        // affix header to the top side, allowing horizontal scroll
        $header.css({top: scrollTop}).show();
      } else {
        $header.hide();
      }

      if (affixLeft){
        // affix sidebar to left side under header, allowing vertical scroll
        $sidebar.css({
          top: headerHeight + (affixTop ? 0 : -1), // (uncontrollable FF border)
          left: scrollLeft
        })
        .show();
      } else {
        $sidebar.hide();
      }

      if (affixLeft || affixTop){
        // affix cornter to top left while scrolling
        $corner.css({
            height: headerHeight + (affixTop ? 1 : 0), // (unconrollable FF border)
            width: sidebarWidth,
            top: affixTop ?  scrollTop : 0,
            left: affixLeft ? scrollLeft : 0
          })
          .show();
      } else {
        $corner.hide();
      }
    }

    $(window).on('scroll resize', updateGrid);
    $('#js-schedule').on('scroll', updateGrid);
  });

}(jQuery);
