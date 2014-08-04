function Choice(data){
  var self = this;
  self.name = ko.observable(data.name);
  self.title = ko.observable(data.title);
}
