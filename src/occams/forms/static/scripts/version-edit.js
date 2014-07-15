/**
 * Form field manager view model
 */
function VersionEditViewModel(){
  var self = this;

  self.isReady = ko.observable(false);        // content loaded flag
  self.isDragging = ko.observable(false);     // view drag state flag

  self.types = ko.observableArray([]);        // available types

  self.name = ko.observable();
  self.title = ko.observable();
  self.description = ko.observable();
  self.publish_date = ko.observable();
  self.retract_date = ko.observable();

  self.fieldsSrc = null;
  self.fields = ko.observableArray([]);       // form fields

  self.selectedEditField = ko.observable();   // currently field being edited
  self.fieldForEditing = ko.observable();     // A copy of the field for editing
  self.selectedDeleteField = ko.observable(); // currently field being edite

  self.hasFields = ko.computed(function(){    // form has no fields flag
    return self.fields().length > 0;
  });

  self.isEditing = ko.computed(function(){
    return !!self.selectedEditField() || !!self.selectedDeleteField();
  });

  self.isMovingEnabled = ko.computed(function(){ // dragging enabled flag
    // we can't just specify this in the isEnabled option
    // because of a bug in knockout, this workaround is sufficient.
    return !self.isEditing();
  });

  self.isSelectedField = function(field){
    return self.isSelectedEditField(field) || self.isSelectedDeleteField(field);
  };

  self.isSelectedEditField = function(field){
    return field === self.selectedEditField();
  };

  self.isSelectedDeleteField = function(field){
    return field === self.selectedDeleteField();
  };

  /**
   * Handler when a new field is added to form
   */
  self.showAddForm = function(type, event, ui){
    var field = new Field({type: type.name()});
    self.selectedEditField(field);
    return field;
  };

  /**
   * Helper method to clear any type of selected field
   */
  self.clearSelected = function(){
    self.selectedEditField(null);
    self.fieldForEditing(null);
    self.selectedDeleteField(null);
  };

  /**
   * Send PUT/POST delete request for the field
   */
  self.saveField = function(field){
    var selected = self.selectedEditField(),
        edited = ko.toJS(this.fieldForEditing()); //clean copy of edited
    $.ajax({
      url: field.id() ? field.__metadata__.src() : self.fieldsSrc,
      method: field.id() ? 'POST' : 'PUT',
      data: edited,
      error: function(jxhr, status, error){
        console.log('THERE WERE PROBLEMS EDITING');
      },
      success: function(data, status, jxhr){
        selected.update(data);
        self.clearSelected();
      }
    });
  };

  /**
   * Selected the field for editing
   */
  self.selectFieldForEditing = function(field) {
    self.selectedEditField(field);
    self.fieldForEditing(new Field(ko.toJS(field)));
  };

  /**
   * Send DELETE request the field
   */
  self.deleteField = function(field){
    $.ajax({
      url: field.__metadata__.src(),
      method: 'DELETE',
      success: function(data, status, jxhr){
        self.fields.destroy(field);
        self.clearSelected();
      }
    });
  };

  // Load initial data
  $.getJSON(window.location, function(data) {
    self.fieldsSrc = data.fields.__metadata__.src
    self.fields(ko.utils.arrayMap(data.fields.items, function(f){
      return new Field(f);
    }));
    self.types(ko.utils.arrayMap(data.__metadata__.types, ko.mapping.fromJS));
    self.isReady(true);
  });
}


/**
 * Field model
 */
function Field(data){
  var self = this;

  self.update(data);

  self.template = ko.computed(function(){
    return self.type() + '-widget-template';
  });

  self.choiceInputType = ko.computed(function(){
    if(self.type() != 'choice'){
      return undefined;
    }
    return self.is_collection() ? 'checkbox' : 'radio';
  });

  self.isSection = ko.computed(function(){
    return self.type() == 'section';
  });
}

// Extend the Field model with commit/revert functionality for editing
ko.utils.extend(Field.prototype, {
  cache: function(){},
  update: function(data) {
    var self = this;
    ko.mapping.fromJS(data, {
      'fields': {
        create: function(options) {
          return new Field(options.data);
        }
      }
    }, self);
    //save off the latest data for later use
    self.cache.latestData = data;
  },
  revert: function() {
    var self = this;
    self.update(self.cache.latestData);
  },
  commit: function() {
    var self = this;
    self.cache.latestData = ko.toJS(self);
  }
});


/**
 * Draggable helper for cloning type selections properly
 */
var newTypeHelper = function(element){
  return $(this)
    .clone()
    .appendTo(document.body)
    .css('width', $(this).width());
};


/**
 * Draggable helper to set start dragging flag
 */
var newTypeDragStart = function(event, ui){
  ko.contextFor(this).$root.isDragging(true);
};


/**
 * Draggable helper to set stop dragging flag
 */
var newTypeDragStop = function(event, ui){
  // Wait a bit so that message doesn't reappear even though dragging was
  // successful
  var tid = setTimeout(function(){
    ko.contextFor(event.target).$root.isDragging(false);
    clearTimeout(tid);
  }, 500);
};


$(document).ready(function(){

  if ($('#version_edit').length <= 0){
    return;
  }

  //
  // enable view model only for the target page
  //
  ko.applyBindings(new VersionEditViewModel());

  //
  // Affix: affix the types menu to follow the user's scrolling.
  //
  +function(){
    var MARGIN_TOP = 20; // use 20 pixels of margin
    $('#of-types')
      .affix({
        offset: {
          top: function(obj){
            // calculate the top offset once the editor is actually rendered
            return (this.top = $(obj.context).parent().offset().top - MARGIN_TOP);
          }
        }
      })
      .on('affix-top.bs.affix', function(event){
        // affixing to the top requires no positioning, use container's width
        return $(this).width('auto');
      })
      .on('affix.bs.affix', function(event){
        // affixing arbitrarily uses fixed positioning, use original width
        return $(this).css('top', MARGIN_TOP).width($(this).width());
      });
    }();
});
