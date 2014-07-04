var socket = io.connect('http://' + document.domain + ':' + location.port);
var detailedLog = []

$( document ).ready(function() {

    window.onbeforeunload = function() {
      return "Are you sure you want to navigate away? This will delete all logged data for this session.";
    }

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

    var add_to_console = function(msg){
        $('#log tr:first').before('<tr><td>' +msg+'</td></tr>');
    }

    var logme = function(msg){
        socket.emit('actionlog', {data: msg});
    }

    socket.on('actionlog', function(msg) {
        add_to_console(msg)
    });


    _updateloglength = _.throttle(function(){
        $('#loglength').html(detailedLog.length);
    }, 5000);

    socket.on('log', function(msg) {
        detailedLog.push(msg);
        _updateloglength()
    });


    _setafewconsolemessages = _.throttle(function(){add_to_console("!Setting forces manually.");}, 1000);
    var setManual = function(){
        left = $('#leftslider').slider( "value" )
        right = $('#rightslider').slider( "value" )
        socket.emit('set_manual', {left:left, right:right});
        _setafewconsolemessages();
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
        if (confirm("Really delete all log data?") == true) {
            detailedLog = []
                    $('#loglength').html(detailedLog.length);
                    add_to_console("!Clear logfile.")
        }
    });

    var getlog = function(){return detailedLog}

    $(".downloadlogbutton").click(function(){
        saveAs(
              new Blob(
                  [csv = CSV.objectToCsv(getlog())]
                , {type: "text/plain;charset=utf-8"}
            )
            , "document.xhtml"
        );
    });

    $(".runbutton").click(function(){
        logme("!Run program.")
        add_to_console("!Run program.")
        socket.emit('new_program', {data: $('#prog').val()});
    });


});
