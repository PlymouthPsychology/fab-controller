var socket = io.connect('http://' + document.domain + ':' + location.port);
window.onbeforeunload = function() {
        return "";
}


$(document).ready(function() {

    // SETUP A TIMER
    var loadedtime = new Date() / 1000;
    timenow = function(){
        return Math.round(new Date() / 1000 - loadedtime);
    }

    // KNOCKOUT.js BINDINGS FOR THE UI - DATA SENT IN JSON FROM THE SERVER

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
         'steps_from_top_L':0, 'steps_from_top_R':0, 'logfile': 'log.txt', 'logfilepath': '~/FAB/logs/'}
    );
    ko.applyBindings(PainDashboardModel);




    // MANAGE THE UI

    // fade interface on connect and disconnect to indicate status
    socket.on('connect', function() {
        $('#appwrapper').fadeTo(1, 1);
        add_to_console("Client connected.");
        socket.emit('ready'); // need to send something or other events not heard properly
    });

    socket.on('disconnect', function() {
        $('#appwrapper').fadeTo(1, .2)
    });



    // PLAYING AUDIO PROMPTS
    socket.on('sayprompt', function(data) {
        add_to_console("Playing prompt: {0}".f(data.hand));
        el = $("#say" + data.hand)[0];
        el.play();
    });


    // DISPLAY AND LOG MESSAGES

    socket.on('actionlog', function(msg) {
        add_to_console(msg);
    });

    consolecursor = $('.console > #insertionpoint');
    $(".selectablewithclick").click(selectText); // auto select all of console to enable copy paste


    function add_to_console(msg){
        $('.console').append('{0}, {1}\n'.f(timenow(), msg));
        set_status_bar(msg);
    };

    function set_status_bar(msg){
        $('.status').html('<p>{0}</p>'.f(msg));
    };

    function updatelogfilename(){
        socket.emit('set_logfile_name', {logfilename: $("#logfilename").val()});
    }

    $("#logfilename").blur(function(){
        updatelogfilename();
    });


    // function for this because otherwise value of log bound at document ready
    // time which means we lose all the data added subsequently
    function getlog(){return $('#console').html()}
    // use external lib to save data as csv, and to a file
    // might need a fairly recent browser
    // note in safari can't force a download - will have to press cmd-S
    $(".downloadlogbutton").click(function(){
        saveAs(
              new Blob(
                  [csv = getlog()]
                , {type: "text/plain;charset=utf-8"}
            )
            , "painmachinelog.csv"
        );
    });


    // MANUAL CONTROL VIA SLIDERS

    // throttle this because on manual dragging it otherwise slows down
    _setafewconsolemessages = _.throttle(function(left, right){
        add_to_console("Target set manually to: {0}/{1}".f(left, right) );
    }, 1000);

    _updatestatusbarwithmanualvalues = _.throttle(function(left, right){
        set_status_bar("Target set manually to: {0}/{1}".f(left, right) );
    }, 100);

    // also throttle this to limit line and log noise
    var setManual = _.throttle(function(event, ui){
        left = $('#leftslider').slider( "value" )
        right = $('#rightslider').slider( "value" )
        socket.emit('set_manual', {left:left, right:right});
        _setafewconsolemessages(left, right);
        _updatestatusbarwithmanualvalues(left, right);
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




    // CALIBRATION CLICK HANDLERS
    function pulse(hand, direction, n){
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



    // OTHER CONTROL CLICK HANDLERS

    $(".stopbutton").bind('click', function(){
        add_to_console("Stopping everything.");
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
        socket.emit('restonfingers', {});
    });

    $("#lift_slightly_button").click(function(){
        add_to_console("Lifting slightly")
        socket.emit('lift_slightly', {});
    });


    $("#runbutton").click(function(){
        // capture program from active program tab
        progtext = $("#programs .active").children('.prog').val()
        add_to_console("Sending program");
        socket.emit('new_program', { data: progtext });
        return true;
    });


    // pain rating buttons
    $(".painscorebutton").click(function(){
        thing = $(this)
        message = "Recorded pain score, {0}, {1}".f(thing.parent().attr('hand'), thing.html());
        add_to_console(message);
        socket.emit('log_session_data', {'message': message});
        return true;
    });


    // make sure we return to the correct tab on refresh
    if (location.hash !== '') $('a[href="' + location.hash + '"]').tab('show');
        return $('a[data-toggle="tab"]').on('shown.bs.tab', function(e) {
        return location.hash = $(e.target).attr('href').substr(1);
    });



    socket.emit('setup complete'); 
});










