(function( $ ){
    $.getLang = function(){
        var lang = '';
        if (navigator.language) {
                lang = navigator.language;
        } else if (navigator.userLanguage){
                lang = navigator.userLanguage;
        }
        return lang;
    };

    $.include = function(prefix, filename) {
        var script = document.createElement('script');
        script.src = prefix + "/" + filename;
        script.type = 'text/javascript';
        $('head').append(script)
    };
})( jQuery );