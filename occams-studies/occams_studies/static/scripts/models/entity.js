function Entity(data){
  var self = this;

  self.__url__ = ko.observable();

  self.id = ko.observable();
  self.schema = ko.observable();
  self.state = ko.observable();
  self.not_done = ko.observable();
  self.collect_date = ko.observable();

  // Useful for UIs where this form can be selected and manipulated
  self.isSelected = ko.observable(false);

  self.isNew = ko.pureComputed(function(){
    return !self.id();
  });

  self.update = function(data){
    data = data || {}
    self.__url__(data.__url__);
    self.id(data.id);
    // Do not use StudyForm, that's intented for STudy UIs and needs to be rethought
    self.schema(data.schema);
    self.state = ko.observable(data.state);
    self.not_done = ko.observable(data.not_done);
    self.collect_date = ko.observable(data.collect_date);
  };

  self.toRest = function(){
    return {
      schema: self.schema() ? self.schema().schema().id : null,
      state: self.state(),
      not_done: self.not_done(),
      collect_date: self.collect_date()
    };
  };

  self.update(data);
}
