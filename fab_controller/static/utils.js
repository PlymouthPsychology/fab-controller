// http://stackoverflow.com/questions/1038746/equivalent-of-string-format-in-jquery
String.prototype.format = String.prototype.f = function() {
    var s = this,
        i = arguments.length;

    while (i--) {
        s = s.replace(new RegExp('\\{' + i + '\\}', 'gm'), arguments[i]);
    }
    return s;
};



// allow selectable logs
function selectText() {
    if (document.selection) {
        var range = document.body.createTextRange();
        range.moveToElementText(this);
        range.select();
    } else if (window.getSelection) {
        var range = document.createRange();
        range.selectNode(this);
        window.getSelection().addRange(range);
    }
}

