var socket = io.connect('http://' + document.domain + ':' + location.port);

$( document ).ready(function() {
    // see http://stackoverflow.com/questions/7704268/formatting-rules-for-numbers-in-knockoutjs
    ko.bindingHandlers.numericText = {
        update: function(element, valueAccessor, allBindingsAccessor) {
           var value = ko.utils.unwrapObservable(valueAccessor()),
               precision = ko.utils.unwrapObservable(allBindingsAccessor().precision) || ko.bindingHandlers.numericText.defaultPrecision,
               formattedValue = value.toFixed(precision);
            ko.bindingHandlers.text.update(element, function() { return formattedValue; });
        },
        defaultPrecision: 0
    };

    //setup the knockout view model with empty data
    var PainDashboardModel = ko.mapping.fromJS(
        {'target_R': 0, 'smooth_R': 0, 'target_L': 0, 'smooth_L': 0, 'remaining': null }
    );
    ko.applyBindings(PainDashboardModel);

    socket.on('connect', function() {
        logme("Client connected.")
        $('#appwrapper').fadeTo(1, 1)
        add_to_console("Client connected.")
    });

    socket.on('disconnect', function() {
        $('#appwrapper').fadeTo(1, .2)
    });

    socket.on('programme_countdown', function(msg) {
        add_to_console(msg.remaining)
    });

    var add_to_console = function(msg){
        $('#log tr:first').before('<tr><td>' +msg+'</td></tr>');
    }

    var logme = function(msg){
        socket.emit('actionlog', {data: msg});
    }

    socket.on('actionlog', function(msg) {
        add_to_console(msg)
    });

    setManual = function(){
        left = $('#leftslider').slider( "value" )
        right = $('#rightslider').slider( "value" )
        socket.emit('set_manual', {left:left, right:right});
    };

    $( "#leftslider" ).slider({slide: setManual, stop: setManual});
    $( "#rightslider" ).slider({slide: setManual, stop: setManual});

    socket.on('update_dash', function(msg) {
        ko.mapping.fromJSON(msg['data'], {}, PainDashboardModel);
        $("#leftslider").slider("value", PainDashboardModel.target_L());
        $("#rightslider").slider("value", PainDashboardModel.target_R());
    });


    // Click handlers
    $(".stopbutton").click(function(){
        add_to_console("!Stop everything")
        logme("!Stop everything")
        socket.emit('stopall', {});
    });

    $(".clearlogbutton").click(function(){
        // $('#log').empty();
        logme("!Clear logfile.")
        add_to_console("!Clear logfile.")
        socket.emit('clear_log', {});
    });

    $(".runbutton").click(function(){
        logme("!Run program.")
        add_to_console("!Run program.")
        socket.emit('new_program', {data: $('#prog').val()});
    });


});
