/**
 * Form field manager view model
 */
function VersionEditorView(fieldsUrl){
  'use strict';

  var self = this;

  self.isReady = ko.observable(false);        // content loaded flag
  self.isDragging = ko.observable(false);     // view drag state flag

  self.availableTypes = ko.observableArray(); // available types

  self.name = ko.observable();
  self.title = ko.observable();
  self.description = ko.observable();
  self.publish_date = ko.observable();
  self.retract_date = ko.observable();

  self.fields = ko.observableArray();

  self.hasFields = ko.pureComputed(function(){    // form has no fields flag
    return self.fields().length > 0;
  });

  self.selectedField = ko.observable();           // currently selected field
  self.editableField = ko.observable();           // a copy of the field for editing

  var EDIT = 'edit', DELETE = 'delete';
  self.modeField = ko.observable();
  self.showEditView = ko.pureComputed(function(){ return self.modeField() == EDIT; });
  self.showDeleteView = ko.pureComputed(function(){ return self.modelField() == DELETE; });

  self.isMovingEnabled = ko.pureComputed(function(){ // dragging enabled flag
    // we can't just specify this in the isEnabled option
    // because of a bug in knockout, this workaround is sufficient.
    return !(self.showEditView() || self.showDeleteView());
  });

  self.isSelectedField = function(field){
    return field === self.selectedField();
  };

  /**
   * Handler when a new field is added to form
   */
  self.startAdd = function(type, event, ui){
    self.startEdit(new Field({type: type.name()}));
  };

  self.startEdit = function(field){
    self.selectedField(field);
    self.editableField(new Field(ko.toJS(field)));
    self.modeField(EDIT);
  };

  self.startDelete = function(field){
    self.selectedField(field);
    self.modeField(DELETE);
  };

  /**
   * Helper method to clear any type of selected field
   */
  self.clear = function(){
    self.selectedField(null);
    self.editableField(null);
    self.modeField(null);
  };

  self.doMoveField = function(arg, event, ui){
    var parent = ko.dataFor(event.target);
    var data = {
      move: 1,
      parent: parent instanceof VersionEditViewModel ? null : parent.name(),
      after: arg.targetIndex > 0 ? arg.targetParent()[arg.targetIndex].name() : null
    };

    if (arg.item.isNew()){
        arg.item.__move__ = data;
        return;
    }

    $.ajax({
        url: arg.item.__url__() + '?move',
        method: 'PUT',
        data: ko.toJSON(data),
        contentType: 'application/json; charset=utf-8',
        headers: {'X-CSRF-Token': $.cookie('csrf_token')},
        error: function(jqXHR, textStatus, errorThrown){
          console.log('Failed to sort, resetting item');
          // put it back
          arg.targetParent.splice(arg.targetIndex, 1);
          arg.sourceParent.splice(arg.sourceIndex, 0, arg.item);
        }
    });
  };

  /**
   * Cancels form edits.
   */
  self.doCancelEdit = function(data, event){
    var selected = self.selectedField();
    if (selected.isNew()){
      var context = ko.contextFor(event.target);
      context.$parentContext.$parent.fields.remove(selected);
    }
    self.clear()
  };

  /**
   * Send PUT/POST delete request for the field
   */
  self.doEditField = function(data, event){
    var $form = $(event.target).closest('form');
    if ($form.validate().form()){
      var selected = self.selectedField,
        data = ko.toJS(self.editableField);

      if (selected.isNew()) {
        $.extend(data, edits.__move__);
      }

      $.ajax({
        url: selected.isNew() ?  fieldFactorySrc : selected.__url__(),
        method: selected.isNew() ? 'POST' : 'PUT',
        contentType: 'application/json; charset=utf-8',
        data: ko.toJSON(data),
        headers: {'X-CSRF-Token': $.cookie('csrf_token')},
        error: handlXHRError({form: $form}),
        beforeSend: function(){
          self.isSaving(true);
        },
        success: function(data, textStatus, jqXHR){
          selected.update(data);
          self.clear();
        },
        complete: function(){
          self.isSaving(false);
        }
      });
    }
  };

  /**
   * Send DELETE request the field
   */
  self.doDeleteField = function(field){
    $.ajax({
      url: field.__url__(),
      method: 'DELETE',
      headers: {'X-CSRF-Token': $.cookie('csrf_token')},
      success: function(data, status, jxhr){
        self.fields.destroy(field);
        self.clear();
      }
    });
  };

  // Load initial data
  $.getJSON(fieldsUrl, function(data) {
    self.fields(data.fields.fields.map(function(f){ return new Field(f); }));
    self.types(data.__types__);
    self.isReady(true);
  });
}

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


/**
 * Affix: affix the types menu to follow the user's scrolling.
 */
function setupTypesAffix(){

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
};
