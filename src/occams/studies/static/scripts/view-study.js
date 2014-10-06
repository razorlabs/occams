
/**
 * Schema representation in the context of a study
 */
function StudySchema(data){
  var self = this;
  self.name = data.name;
  self.title = data.title
  self.versions = ko.observableArray(data.versions);
}


/**
 * Cycle representation in the context of a study
 */
function StudyCycle(data){
  var self = this;

  self.update = function(data){
    self.id(data.id);
    self.name
  };

  self.id = ko.observable(data.id);
  self.name = ko.observable(data.name);
  self.title = ko.observable(data.title);
  self.week = ko.observable(data.week);
  self.is_interim = ko.observable(data.is_interim);

  self.schemata = ko.observableArray((data.schemata || []).map(function(schema){
    return new StudySchema(schema);
  }));

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

  //self.selectedForms = ko.observableArray();
  //self.hasSelectedForms = ko.computed(function(){
    //return self.selectedForms().length > 0;
  //});

  //self.onClickForm = function(item, event){
    //var $element = $(event.target)
      //, value = $element.val();
    //if ($element.prop('checked')){
      //console.log('adding', value);
      //self.selectedForms.push(value);
    //} else {
      //console.log('removing', value);
      //self.selectedForms.remove(value);
    //}
    //return true;
  //}

  //self.startFormAdd = function(){
  //};

  //self.startEdit = function(){
  //};

  //self.startDelete = function(){
  //};

  self.toggleGrid = function(data, event){
    console.log(event);
  };

  self.isReady(true);
}

+function($){
  $(document).ready(function(){
    var $view = $('#view-study')[0];
    if ($view){
      ko.applyBindings(new StudyView(), $view);
    }
  });
}(jQuery);
