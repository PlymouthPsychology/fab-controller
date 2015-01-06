var socket = io.connect('http://' + document.domain + ':' + location.port);

// this is the client side log structure which gets exported to csv from within the browser
// we don't keep logs on the pi because it might get too big if the machine is left on and do
// nasty things
var detailedLog = []

$(document).ready(function() {

    // window.onbeforeunload = function() {
    //   return "Are you sure you want to navigate away? This will delete all logged data for this session.";
    // }

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

    //setup the knockout view model with empty data - this is to allow declarative
    //data bindings from json which comes in to html elements in the page
    //the first command sets up the model bindings from dummy json.
    var PainDashboardModel = ko.mapping.fromJS(
        { 'version': "0.0", 'target_R': 0, 'sensor_R': 0, 'target_L': 0, 'sensor_L': 0, 'remaining': null,
         'steps_from_top_L':0, 'steps_from_top_R':0, 'logfile': 'log.txt'}
    );
    ko.applyBindings(PainDashboardModel);

    // fade interface on connect and disconnect to indicate status
    socket.on('connect', function() {
        $('#appwrapper').fadeTo(1, 1);
        add_to_console("Client connected.");
    });

    socket.on('disconnect', function() {
        $('#appwrapper').fadeTo(1, .2)
    });


    var add_to_console = function(msg){
        $('#console p:first').before('<p>' + msg +'</p>');
    }

    socket.on('actionlog', function(msg) {
        add_to_console(msg);
    });


    // throttle this because on manual dragging it otherwise slows down
    _setafewconsolemessages = _.throttle(function(){add_to_console("Setting target manually.");}, 1000);

    // also throttle this to limit line and log noise
    var setManual = _.throttle(function(event, ui){
        left = $('#leftslider').slider( "value" )
        right = $('#rightslider').slider( "value" )
        socket.emit('set_manual', {left:left, right:right});
        _setafewconsolemessages();
    }, 10);

    // setup sliders for manual control
    $( "#leftslider" ).slider({min: 0, max: 2000, slide: setManual, stop: setManual});
    $( "#rightslider" ).slider({min: 0, max: 2000, slide: setManual, stop: setManual});

    // apply json to knockout model and update sliders manually because they
    // don't have a knockout binding yet
    socket.on('update_dash', function(msg) {
        ko.mapping.fromJSON(msg['data'], {}, PainDashboardModel);
        $("#leftslider").slider("value", PainDashboardModel.target_L());
        $("#rightslider").slider("value", PainDashboardModel.target_R());
    });


    // CLICK HANDLERS


    pulse = function(hand, direction, n){
    socket.emit('manual_pulse', {hand: hand, direction: direction, n: n});
        add_to_console("Manual pulses sent");
    }

    $("#zerobutton").click(function(){
        add_to_console("Zero'd sensors");
        socket.emit('zero_sensor', {});
    });



    $("#toggle_tracking_button").click(function(){
        add_to_console("Toggle tracking");
        socket.emit('toggle_tracking', {});
    });


    $("#left_2kg_button").click(function(){
        add_to_console("Set 2kg for left");
        socket.emit('mark_twokg', {hand: 'left'});
    });

    $("#right_2kg_button").click(function(){
        add_to_console("Set 2kg for right");
        socket.emit('mark_twokg', {hand: 'right'});
    });




    $("#left_pulse_down_button").mousehold(function(i) {
        add_to_console("Pulse left down");
        socket.emit('manual_pulse', {direction: 'down', hand: 'left', n: 1});
    });

    $("#right_pulse_down_button").mousehold(function(i) {
        add_to_console("Pulse right down");
        socket.emit('manual_pulse', {direction: 'down', hand: 'right', n: 1});
    });

    $("#left_pulse_up_button").mousehold(function(i) {
        add_to_console("Pulse left up");
        socket.emit('manual_pulse', {direction: 'up', hand: 'left', n: 1});
    });

    $("#right_pulse_up_button").mousehold(function(i) {
        add_to_console("Pulse right up");
        socket.emit('manual_pulse', {direction: 'up', hand: 'right', n: 1});
    });

    $("#stopbutton").bind('click', function(){
        add_to_console("Stopping everything");
        socket.emit('stopall', {});
        socket.emit('lift_slightly', {});
    });

    
    $("#quitbutton").bind('click', function(){
        if (confirm("Quit now?")) {
            socket.emit('quit', {});
            window.close();
            
        }
    });


    $("#return_to_stops_button").click(function(){
        add_to_console("Returning pistons to top stops.")
        socket.emit('return_to_stops', {});
    });

    $("#getsetbutton").click(function(){
        add_to_console("Rest crushers on fingers")
        socket.emit('restonfingers', {});
    });

    $("#lift_slightly_button").click(function(){
        add_to_console("Lifting slightly")
        socket.emit('lift_slightly', {});
    });

    function updatelogfilename(){
        socket.emit('set_logfile_name', {logfilename: $("#logfilename").val()});
    }

    $("#logfilename").blur(function(){
        add_to_console("Updating logfile name to " + $("#logfilename").val())
        updatelogfilename();
    });


    // function for this because otherwise value of log bound at document ready
    // time which means we lose all the data added subsequently
    var getlog = function(){return detailedLog}
    // use external lib to save data as csv, and to a file
    // might need a fairly recent browser
    // note in safari can't force a download - will have to press cmd-S
    $(".downloadlogbutton").click(function(){
        saveAs(
              new Blob(
                  [csv = CSV.objectToCsv(getlog())]
                , {type: "text/plain;charset=utf-8"}
            )
            , "painmachinelog.csv"
        );
    });


    $("#runbutton").click(function(){
        add_to_console("Running program.");
        socket.emit('new_program', { data: $('#prog').val() });
        return true;
    });


    socket.emit('log_session_data', {'message': 'Connected.'});

});
