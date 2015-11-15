$(function(){
  var bins;

  function setMessage(msg) {
    $("#message").html(msg);
  }

  $("#find-me").click(function() {
    var coords;
    var grid;

    $("#find-me").hide();
    setMessage("Locating...");

    $.getJSON("json/grid.json",function(d) {
      grid = d;
      console.log("got grid");
      finish();
    });

    navigator.geolocation.getCurrentPosition(function(p) {
      coords = p.coords;
      finish();
    },function(e) {setMessage(e.message||"Couldn't get location for some reason.");});

    function finish() {
      if (!coords || !grid) {
        return;
      }

      var myTemp = getTemp();
      if (myTemp == null) {
        setMessage("Couldn't get a forecast. Are you in the continental US?")
      } else {
        var totalPop = bins.pluck(1).sum();
        var colderPop = bins.filter(function(d) {return d[0]<myTemp;}).pluck(1).sum();
        var warmerPop = bins.filter(function(d) {return d[0]>myTemp;}).pluck(1).sum();
        $("#bin-"+myTemp).css({background:'red'})
        var adj,pop;
        if (colderPop>warmerPop) {
          adj = "warmer";
          pop = colderPop;
        } else {
          adj = "colder";
          pop = warmerPop;
        }
        setMessage("Your high temperature today is "+adj+" than for "+Math.round(1000*pop/totalPop)/10+
                    "% of residents of the continental US.");
      }
    }

    function getTemp() {
      var ourxy = proj4(grid.proj,[coords.longitude,coords.latitude]);
      var firstxy = proj4(grid.proj,[grid.firstLon,grid.firstLat]);
      var gridx = Math.round((ourxy[0]-firstxy[0])/grid.dx);
      var gridy = Math.round((ourxy[1]-firstxy[1])/grid.dy);
      var foo = grid.values[gridy];
      if (foo) {
        return foo[gridx]
      }
    }
  });

  $.getJSON("json/histogram.json",function(d) {
    bins = _(d.tempbins);
    var temps = bins.pluck(0);
    var minTemp = temps.min();
    var maxTemp = temps.max();
    var binWidth = 100/(maxTemp+1-minTemp);
    var maxPop = bins.pluck(1).max();
    $chart = $(".chart")
    bins.forEach(function(b) {
      $('<div class="bin">')
        .css({
          width: 1.01*binWidth+"%;",
          height: 100*b[1]/maxPop + "%",
          left: (b[0]-minTemp)*binWidth + "%"
        })
        .attr('id','bin-'+b[0])
        .appendTo($chart);
    }).value() //need this value() because forEach is lazy
  })
});