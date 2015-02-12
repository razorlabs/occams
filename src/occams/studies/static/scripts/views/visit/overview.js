function VisitView(options){
  "use strict";
  var self = this;

  self.isReady = ko.observable(false);
  self.isSaving = ko.observable(false);

  self.selectedItem = ko.observable();  // originally selected item
  self.editableItem = ko.observable();  // pending changes (will be applied to selected)

  self.errorMessage = ko.observable();

  var VIEW = 'view', ADD = 'add', EDIT = 'edit', DELETE = 'delete';

  self.visit = new Visit(options.visitData);

  self.statusVisit = ko.observable();
  self.showEditVisit = ko.pureComputed(function(){ return self.statusVisit() == EDIT; });
  self.showDeleteVisit = ko.pureComputed(function(){ return self.statusVisit() == DELETE; });

  // Forms UI settings
  self.statusForm = ko.observable();
  self.showAddForm = ko.pureComputed(function(){ return self.statusForm() == ADD; });

  self.selectedForms = ko.observableArray();

  self.hasSelectedForms = ko.pureComputed(function(){
    return self.selectedForms().length > 0;
  });

  self.clear = function(){
    self.errorMessage(null);
    self.selectedItem(null);
    self.editableItem(null);
    self.statusVisit(null);
    self.statusForm(null);
  };

  self.onClickForm = function(item, event){
    var $element = $(event.target)
      , value = $element.val();
    if ($element.prop('checked')){
      console.log('adding', value);
      self.selectedForms.push(value);
    } else {
      console.log('removing', value);
      self.selectedForms.remove(value);
    }
    return true;
  };

  self.startEdit = function(){
    self.clear();
    self.statusVisit(EDIT);
    self.editableItem(new Visit(ko.toJS(self.visit)));
  };

  self.startDelete = function(){
    self.clear();
    self.statusVisit(DELETE);
  };

  self.startFormAdd = function(){
    self.clear();
    self.statusForm(ADD);
    self.editableItem(new Entity());
  };

  self.saveVisit = function(element){
    if ($(element).validate().form()){
      $.ajax({
        url: self.visit.__url__(),
        method: 'PUT',
        contentType: 'application/json; charset=utf-8',
        data: ko.toJSON(self.editableItem().toRest()),
        headers: {'X-CSRF-Token': $.cookie('csrf_token')},
        error: handleXHRError({form: element, logger: self.errorMessage}),
        beforeSend: function(){
          self.isSaving(true);
        },
        success: function(data, textStatus, jqXHR){
          self.visit.update(data);
          self.clear();
        },
        complete: function(){
          self.isSaving(false);
        }
      });
    }
  };

  self.deleteVisit = function(element){
    $.ajax({
      url: self.visit.__url__(),
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

  self.isReady(true);
}


/**
 * Global select2 options generator for the target cycle field
 *
 * The reason this is global is because it also needs to be access from the patient view.
 */
function cycleSelect2Options(element){
  "use strict";
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
          results: data.cycles.map(function(cycle_data){
            return new Cycle(cycle_data);
          })
        };
      },
    }
  }
}


