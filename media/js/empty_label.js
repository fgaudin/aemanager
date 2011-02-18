(function( $ ){
    $.fn.fillLabel = function(label){
        return this.each(function() {
            var $this = $(this);
            var value = $(label).text();
            value = value.replace(':','');
            value = $.trim(value);
            $this.val(value);
            $this.addClass('empty-field');
        });
    };

    $.fn.bindRowEvents = function() {
    return this.each(function() {
      var $this = $(this);

      var label = $this.prev('.inline-label');
      if ($this.val() == '') {
          $this.fillLabel(label);
      }
      $(label).css('display', 'none');

      $this.focusin(function(e){
          e.preventDefault();
          if ($(e.currentTarget).hasClass('empty-field')) {
              $(e.currentTarget).removeClass('empty-field');
              $(e.currentTarget).val('');
          }
      });

      $this.focusout(function(e){
          e.preventDefault();
          if (!$(e.currentTarget).hasClass('empty-field') && $(e.currentTarget).val() == '') {
              var label = $(e.currentTarget).prev('.inline-label');
              $(e.currentTarget).fillLabel(label);
          }
      });
    });
  };
})( jQuery );