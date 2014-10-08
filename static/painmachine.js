var socket = io.connect('http://' + document.domain + ':' + location.port);

// this is the client side log structure which gets exported to csv from within the browser
// we don't keep logs on the pi because it might get too big if the machine is left on and do
// nasty things
var detailedLog = []

$( document ).ready(function() {

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
        {'target_R': 0, 'sensor_R': 0, 'target_L': 0, 'sensor_L': 0, 'remaining': null,
         'true_L':0, 'true_R':0 }
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
        $('#log tr:first').before('<tr><td>' +msg+'</td></tr>');
    }

    socket.on('actionlog', function(msg) {
        add_to_console(msg)
    });


    // show how many lines long the log is. Throttle to avoid annoyance in UI
    _updateloglength = _.throttle(function(){
        $('#loglength').html(detailedLog.length);
    }, 5000);

    // append to log when mesages recieved
    socket.on('log', function(msg) {
        detailedLog.push(msg);
        _updateloglength()
    });


    // throttle this because on manual dragging it otherwise slows down
    _setafewconsolemessages = _.throttle(function(){add_to_console("! Setting forces manually.");}, 1000);

    // also throttle this to limit line and log noise
    var setManual = _.throttle(function(event, ui){
        left = $('#leftslider').slider( "value" )
        right = $('#rightslider').slider( "value" )
        socket.emit('set_manual', {left:left, right:right});
        _setafewconsolemessages();
    }, 10);

    // setup sliders for manual control
    $( "#leftslider" ).slider({min:0, max:2000, slide: setManual, stop: setManual});
    $( "#rightslider" ).slider({min:0, max:2000, slide: setManual, stop: setManual});

    // apply json to knockout model and update sliders manually because they
    // don't have a knockout binding yet
    socket.on('update_dash', function(msg) {
        ko.mapping.fromJSON(msg['data'], {}, PainDashboardModel);
        $("#leftslider").slider("value", PainDashboardModel.target_L());
        $("#rightslider").slider("value", PainDashboardModel.target_R());
    });


    // CLICK HANDLERS


    $("#zerobutton").click(function(){
        add_to_console("Zero'd sensors");
        socket.emit('zero_sensor', {});
    });


    $("#left_2kg_button").click(function(){
        add_to_console("Set 2kg for left");
        socket.emit('mark_twokg', {hand: 'left'});
    });

    $("#right_2kg_button").click(function(){
        add_to_console("Set 2kg for right");
        socket.emit('mark_twokg', {hand: 'right'});
    });

    $("#stopbutton").click(function(){
        add_to_console("!Stop everything")
        socket.emit('stopall', {});
        socket.emit('lift_slightly', {});
        socket.emit('lift_slightly', {});
    });

    $("#getsetbutton").click(function(){
        add_to_console("Rest crushers on fingers")
        socket.emit('restonfingers', {});
    });

    $("#lift_slightly_button").click(function(){
        add_to_console("Lifting slightly")
        socket.emit('lift_slightly', {});
    });

    // $("#resetbutton").click(function(){
    //     add_to_console("Reset")
    //     socket.emit('bothgototop', {});
    // });

    $(".clearlogbutton").click(function(){
        if (confirm("Really delete all log data?") == true) {
            detailedLog = []
                    $('#loglength').html(detailedLog.length);
                    add_to_console("! Clearing logfile.")
        }
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


    $(".runbutton").click(function(){
        add_to_console("! Run program.")
        socket.emit('new_program', {data: $('#prog').val()});
    });


});
