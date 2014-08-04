/**
 * Form field manager view model
 */
function VersionEditViewModel(){
  var self = this;

  self.isReady = ko.observable(false);        // content loaded flag
  self.isDragging = ko.observable(false);     // view drag state flag

  self.listingSrc = null;
  self.types = ko.observableArray([]);        // available types

  self.name = ko.observable();
  self.title = ko.observable();
  self.description = ko.observable();
  self.publish_date = ko.observable();
  self.retract_date = ko.observable();

  self.fields = ko.observableArray([]);

  self.hasFields = ko.computed(function(){    // form has no fields flag
    return self.fields().length > 0;
  });

  self.selectedField = ko.observable();            // currently selected field
  self.selectedFieldForEditing = ko.observable();  // a copy of the field for editing
  self.showEditView = ko.observable(false);
  self.showDeleteView = ko.observable(false);

  self.isMovingEnabled = ko.computed(function(){ // dragging enabled flag
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
    var field = new Field({isNew: true, __src__: self.listingSrc, type: type.name()});
    self.startEdit(field);
    return field;
  };

  self.startEdit = function(field){
    self.clearSelected();
    self.selectedField(field);
    self.selectedFieldForEditing(new Field(field.toJS()));
    self.showEditView(true);
  };

  self.startDelete = function(field){
    self.clearSelected();
    self.selectedField(field);
    self.showDeleteView(true);
  };

  /**
   * Helper method to clear any type of selected field
   */
  self.clearSelected = function(){
    self.selectedField(null);
    self.selectedFieldForEditing(null);
    self.showEditView(false);
    self.showDeleteView(false);
  };

  self.doMoveField = function(arg, event, ui){
    var parent = ko.dataFor(event.target);
    var data = {
      move: 1,
      parent: parent instanceof VersionEditViewModel ? null : parent.name(),
      after: arg.targetIndex > 0 ? arg.targetParent()[arg.targetIndex].name() : null
    };

    if (arg.item.isNew()){
        console.log('moved new', arg.item);
        arg.item.__move__ = data;
        return;
    }

    $.ajax({
        url: arg.item.__src__() + '?move',
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
    self.clearSelected()
  };

  /**
   * Send PUT/POST delete request for the field
   */
  self.doEditField = function(data, event){
    var $form = $(event.target).closest('form');

    // Make sure it's valid before sending data to server
    if (!$form.validate().form()){
      return;
    }

    var edits = self.selectedFieldForEditing()
      , data = edits.toJS();

    if (edits.isNew()){
      $.extend(data, edits.__move__);
      console.log(data);
    }

    self.selectedFieldForEditing().isSaving(true);

    $.ajax({
      url: edits.__src__(),
      method: edits.isNew() ? 'POST' : 'PUT',
      contentType: 'application/json; charset=utf-8',
      data: ko.toJSON(data),
      headers: {'X-CSRF-Token': $.cookie('csrf_token')},
      error: function(jqXHR, textStatus, errorThrown){
        var data = jqXHR.responseJSON;
        if (!data || !data.validation_errors){
            console.log('A server error occurred');
            return
        }
        console.log('A recoverable error occurred')
        console.log(data);
      },
      success: function(data, textStatus, jqXHR){
        self.selectedField().update(data);
        self.clearSelected();
      },
      complete: function(){
        if (self.selectedFieldForEditing()){
          self.selectedFieldForEditing().isSaving(false);
        }
      }
    });
  };

  /**
   * Send DELETE request the field
   */
  self.doDeleteField = function(field){
    $.ajax({
      url: field.__src__(),
      method: 'DELETE',
      headers: {'X-CSRF-Token': $.cookie('csrf_token')},
      success: function(data, status, jxhr){
        self.fields.destroy(field);
        self.clearSelected();
      }
    });
  };

  // Load initial data
  $.getJSON(window.location, function(data) {
    self.listingSrc = data.fields.__src__
    self.fields(ko.utils.arrayMap(data.fields.fields, function(f){
        return new Field(f);
    }));
    self.types(ko.utils.arrayMap(data.__types__, ko.mapping.fromJS));
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


$(document).ready(function(){

  if ($('#version_editor').length <= 0){
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

/**
 * Form field manager view model
 */
function VersionViewModel(){
  var self = this;

  self.isReady = ko.observable(true);        // content loaded flag

  self.isDrafting = ko.observable(false);
  self.isDeleting = ko.observable(false);

  self.showDraftView = ko.observable(false);
  self.showDeleteView = ko.observable(false);

  // We don't load anything so we need to inspect the
  // contents for the source targets
  self.deleteSrc = $('#delete-button').data('target');
  self.draftSrc = $('#delete-button').data('target');

  self.clearSelected = function(){
    self.showDeleteView(false);
    self.showDraftView(false);
  };

  self.startDraftView = function(){
    self.clearSelected();
    self.showDraftView(true);
  };

  self.startDeleteView = function() {
    self.clearSelected();
    self.showDeleteView(true);
  };

  /**
   * Sends a draft request for the current version of the form.
   */
  self.doDraftForm = function(form){
    self.isDrafting(true);
    $.ajax({
      url: self.draftSrc,
      method: 'POST',
      data: {draft: 1},
      headers: {'X-CSRF-Token': $.cookie('csrf_token')},
      error: function(jqXHR, textStatus, errorThrown){
        console.log('An error occurred, need to show something...');
      },
      success: function(data, textStatus, jqXHR){
        window.location = data.__next__;
      }
    });
  };

  /**
   * Sends a delete request for the current version of the form.
   */
  self.doDeleteForm = function(form){
    self.isDeleting(true);
    $.ajax({
      url: self.deleteSrc,
      method: 'DELETE',
      headers: {'X-CSRF-Token': $.cookie('csrf_token')},
      error: function(jqXHR, textStatus, errorThrown){
        console.log('An error occurred, need to show something...');
      },
      success: function(data, textStatus, jqXHR){
        window.location = data.__next__;
      }
    });
  };

}

$(document).ready(function(){
  if ($('#version_preview,#version_view').length < 1){
    return;
  }

  ko.applyBindings(new VersionViewModel());

  $('#delete-modal').on('show.bs.modal', function(event){
    $(this).find('form')[0].reset();
  });
});
