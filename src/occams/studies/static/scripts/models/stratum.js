function Stratum(data){
  'use strict';

  var self = this;

  self.__url__ = ko.observable();
  self.id = ko.observable();
  self.study = ko.observable();
  self.arm = ko.observable();
  self.label = ko.observable();
  self.block_number = ko.observable();
  self.randid = ko.observable();

  self.update = function(data){
    self.__url__(data.__url__);
    self.id(data.id);
    self.study(data.study ? new Study(data.study) : null);
    self.arm(data.arm ? new Arm(data.arm) : null);
    self.label(data.label);
    self.block_number(data.block_number);
    self.randid(data.randid);
  };

  self.update(data || {});
}
