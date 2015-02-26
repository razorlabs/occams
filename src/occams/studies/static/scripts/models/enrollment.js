function Enrollment(data){
  'use strict';

  var self = this;

  self.__url__ = ko.observable();
  self.__randomization_url__ = ko.observable();
  self.__termination_url__ = ko.observable();
  self.__can_edit__ = ko.observable();
  self.__can_terminate__ = ko.observable();
  self.__can_randomize__ = ko.observable();
  self.__can_delete__ = ko.observable();
  self.id = ko.observable();
  self.study = ko.observable();
  self.consent_date = ko.observable();
  self.latest_consent_date = ko.observable();
  self.termination_date = ko.observable();
  self.reference_number = ko.observable();
  self.stratum = ko.observable();

  // Dynamically loaded markup for modal window
  self.termination_ui = ko.observable();
  self.randomization_ui = ko.observable();

  self.isNew = ko.pureComputed(function(){
    return !self.id();
  });

  self.isRandomized = ko.pureComputed(function(){
    var study = self.study(),
        stratum = self.stratum() || {};

    if (!study || !study.is_randomized()){
      return false;
    }

    return stratum && !!stratum.randid();
  });

  self.update = function(data){
    data = data || {};
    self.__url__(data.__url__);
    self.__randomization_url__(data.__randomization_url__);
    self.__termination_url__(data.__termination_url__);
    self.__can_edit__(data.__can_edit__);
    self.__can_terminate__(data.__can_terminate__);
    self.__can_randomize__(data.__can_randomize__);
    self.__can_delete__(data.__can_delete__);
    self.id(data.id);
    self.study(data.study ? new Study(data.study) : null);
    self.consent_date(data.consent_date);
    self.latest_consent_date(data.latest_consent_date);
    self.termination_date(data.termination_date);
    self.reference_number(data.reference_number);
    self.stratum(data.stratum ? new Stratum(data.stratum) : null);
  };

  self.update(data);
}
