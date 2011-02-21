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

    $.fn.labelInside = function() {
    return $(this).each(function() {
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

  $.fn.proposalOverview = function(title, url){
      return $(this).each(function(){
          var $this = $(this);
          $this.change(function(){
              var id = jQuery(this).val();
              if (id) {
                  var get_url = url.replace('0',id) + '?ajax=true';
                  var offset = jQuery(this).offset();
                  $.get(get_url, function(data){
                      $(data).dialog({
                          width: 450,
                          position: [offset.left+100, offset.top-550],
                          title: title});
                  });
                  // and check balance payments if needed
                  if ($('.proposal-field option:selected[value="' + id + '"]').parent('.proposal-field').nextAll('.balance-payments-field:checked').length) {
                      $this.nextAll('.balance-payments-field').attr('checked', true);
                  }
              }
          });
      });
  };

  $.fn.rowHelp = function(){
      return $(this).each(function(){
          var $this = $(this);
          $this.tooltip({
              bodyHandler: function() {
                  return $this.nextAll('.help_text').html();
                },
                delay: 0,
                showURL: false
          });
      });
  };

  $.fn.balanceAll = function(){
      return $(this).each(function(){
          var $this = $(this);
          $this.click(function(e){
              var proposal = $(e.currentTarget).prevAll('.proposal-field');
              if (proposal.val()) {
                  var state = $(e.currentTarget).attr('checked');
                  $('.proposal-field option:selected[value="' + proposal.val() + '"]').each(function(){
                      $(this).parent('.proposal-field').nextAll('.balance-payments-field').attr('checked',state);
                  });
              }
          });
      });
  };
})( jQuery );