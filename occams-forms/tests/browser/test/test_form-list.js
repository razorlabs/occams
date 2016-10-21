var assert = chai.assert;



describe('FormListView', function(){

  function makeOne(){
    return new FormListView()
  }

  beforeEach(function(){
    sinon.spy($, 'getJSON');
  });

  afterEach(function(){
    $.getJSON.restore();
  });

  describe('#filteredForms()', function(){

    var data = [
        {name: 'foo', title: 'ABC', versions: [{status: 'published', publish_date: '2014-07-30', retract_date: null}]}
      , {name: 'bar', title: 'DEF', versions: [{status: 'retracted', publish_date: '2010-05-01', retract_date: '2013-08-01'}]}
      , {name: 'baz', title: 'GHI', versions: [{status: 'draft', publish_date: null, retract_date: null}]}
    ];

    it('should list all forms if not filter is active', function(){
      var view = makeOne();
      view.forms($.map(data, ko.mapping.fromJS));
      assert.isUndefined(view.filter());
      assert.equal(data.length, view.filteredForms().length);
    });

    it('should filter by name', function(){
      var view = makeOne();
      view.forms($.map(data, ko.mapping.fromJS))
      view.filter('foo');
      assert.equal(1, view.filteredForms().length);
      assert.equal('foo', view.filteredForms()[0].name());
    });

    it('should filter by title', function(){
      var view = makeOne();
      view.forms($.map(data, ko.mapping.fromJS))
      view.filter('def');
      assert.equal(1, view.filteredForms().length);
      assert.equal('bar', view.filteredForms()[0].name());
    });

    it('should filter by a version\'s status', function(){
      var view = makeOne();
      view.forms($.map(data, ko.mapping.fromJS))
      view.filter('draft');
      assert.equal(1, view.filteredForms().length);
      assert.equal('baz', view.filteredForms()[0].name());
    });

    it('should filter by p version\'s publish date', function(){
      var view = makeOne();
      view.forms($.map(data, ko.mapping.fromJS))
      view.filter('2014-07-30');
      assert.equal(1, view.filteredForms().length);
      assert.equal('foo', view.filteredForms()[0].name());
    });

    it('should filter by p version\'s retract date', function(){
      var view = makeOne();
      view.forms($.map(data, ko.mapping.fromJS))
      view.filter('2013-08-01');
      assert.equal(1, view.filteredForms().length);
      assert.equal('bar', view.filteredForms()[0].name());
    });

  });

});

