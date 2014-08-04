/**
 * Field model
 */
function Field(data){
  var self = this;

  self.__src__ = ko.observable();
  self.id = ko.observable();
  self.name = ko.observable();
  self.title = ko.observable();
  self.description = ko.observable();
  self.type = ko.observable();
  self.is_required = ko.observable();
  self.is_collection = ko.observable();
  self.is_private = ko.observable();
  self.is_shuffled = ko.observable();
  self.is_readonly = ko.observable();
  self.is_system = ko.observable();
  self.pattern = ko.observable();
  self.decimal_places = ko.observable();
  self.value_min = ko.observable();
  self.value_max = ko.observable();
  self.choices = ko.observableArray([]);

  self.isSaving = ko.observable(false);

  self.isNew = ko.computed(function(){
    return !self.id();
  });

  self.isType = function(){
    for (var i = 0; i < arguments.length; i++){
      if (arguments[i] == self.type()){
        return true;
      }
    }
    return false;
  };

  self.makeValidateOptions = function(){
    return {
      errorClass: 'has-error',
      validClass: 'has-success',
      wrapper: 'p',
      errorPlacement: function(label, element){
        label.addClass('help-block').insertAfter(element);
      },
      onfocusout: function(element, event){
        $(element).valid();
      },
      highlight: function(element, errorClass, validClass){
        $(element)
          .closest('.js-validation-group,.form-group')
          .addClass(errorClass)
          .removeClass(validClass);
      },
      unhighlight: function(element, errorClass, validClass){
        $(element)
          .closest('.js-validation-group,.form-group')
          .addClass(validClass)
          .removeClass(errorClass);
      },
      rules: {
        name: {
          remote: {
             url: self.__src__() + '?' + $.param({validate: 'name'}),
             type: 'POST',
             headers: {'X-CSRF-Token': $.cookie('csrf_token')},
          }
        }
      }
    }
  };

  self.isLimitAllowed = ko.computed(function(){
    return self.isType('string', 'number')
      || (self.isType('choice') && self.is_collection());
  });

  self.choiceInputType = ko.computed(function(){
    return self.is_collection() ? 'checkbox' : 'radio';
  });

  self.isSection = ko.computed(function(){
    return self.type() == 'section';
  });

  self.doAddChoice = function(){
    self.choices.push(new Choice({}));
  };

  self.doDeleteChoice = function(data, event){
      self.choices.remove(data);
  };

  self.update = function(data) {
    ko.mapping.fromJS(data, {
      'fields': {
        create: function(options) {
          return new Field(options.data);
        }
      },
      'choices': {
        create: function(options) {
          return new Choice(options.data);
        }
      }
    }, self);
  };

  self.toJS = function(){
    return ko.mapping.toJS(self, {
      'include': ['__src__',
                  'id', 'name', 'title', 'description', 'type',
                  'is_required', 'is_collection', 'is_private', 'is_shuffled',
                  'is_readonly', 'is_system', 'pattern', 'decimal_places',
                  'value_min', 'value_max', 'choices'],
    });
  }

  self.update(data);
}
