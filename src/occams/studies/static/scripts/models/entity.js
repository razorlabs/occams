function Entity(data){
  var self = this;

  self.__url__ = ko.observable();

  self.id = ko.observable();
  self.schema = ko.observable();
  self.status = ko.observable();
  self.not_done = ko.observable();
  self.collect_date = ko.observable();

  self.isNew = ko.pureComputed(function(){
    return !self.id();
  });

  self.update = function(data){
    data = data || {}
    self.__url__(data.__url__);
    self.id(data.id);
    self.schema(data.schema ? new StudyForm(data.schema) : null);
    self.status = ko.observable(data.status);
    self.not_done = ko.observable(data.not_done);
    self.collect_date = ko.observable(data.collect_date);
  };

  self.toRest = function(){
    return {
      schema: self.schema() ? self.schema().schema().id : null,
      status: self.status(),
      not_done: self.not_done(),
      collect_date: self.collect_date()
    };
  };

  self.update(data);
}
