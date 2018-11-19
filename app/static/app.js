var app = angular.module('toppmart', []);

// replace curly braces with @@ (collides w/ rendering engine)
app.config(function($interpolateProvider) {
    $interpolateProvider.startSymbol('@@')
    $interpolateProvider.endSymbol('@@');
});

app.controller('MainCtrl', function($scope, $http, $timeout) {
    var loadTime = 5000,
    errorCount = 0, // Counter for the server errors
    last_date = Date.now(),
    sidebar_id, // last id of request
    loadPromise; // Pointer to the promise created by the Angular $timeout service
    
    
    format_time = function(total_seconds) {
        total_seconds = Math.floor(total_seconds);
        var hours = (total_seconds / 3600) | 0;
        total_seconds -= hours * 3600;
        var minutes = (total_seconds/60) | 0;
        total_seconds -= minutes * 60;
        return (hours < 10 ? '0' : '') + hours + ':' + (minutes < 10 ? '0' : '') + minutes + ':' + (total_seconds < 10 ? '0' : '') + total_seconds;
    }
    
    var getPlayers = function() {
        $http.get('/sim/json/in_sim')
        .then(function(res) {
          if(sidebar_id == null || sidebar_id != res.data.id) {
              if(res.data.players.length == 0) {
                   $scope.numplayers = '0 players';
                   $scope.players = [];
              } else {
                  for(var i = 0; i < res.data.players.length; i++) {
                      res.data.players[i].width = Math.min(10 + (210 * res.data.players[i].elapsed/res.data.max_time), 220);
                      res.data.players[i].elapsed_formatted = format_time(res.data.players[i].elapsed);
                  }
                  $scope.numplayers = res.data.players.length + ' player' + (res.data.players.length > 1 ? 's' : '');
                  $scope.players = res.data.players;
                  $scope.max_time = res.data.max_time;
                  sidebar_id = res.data.id;
              }
          }
          errorCount = 0;
          nextLoad();
        })
        .catch(function(res) {
          nextLoad(++errorCount * 2 * loadTime);
        });
    };
    
    var updateUI = function() {
        players = $scope.players;
        elapsed = (Date.now() - last_date)/1000;
        $scope.max_time += elapsed;
        $scope.max_time = Math.floor($scope.max_time);
        for(var i = 0; i < players.length; i++) {
            players[i].elapsed += elapsed;
            players[i].width = Math.min(10 + (210 * players[i].elapsed/$scope.max_time), 220);
            players[i].elapsed_formatted = format_time(players[i].elapsed);
        }
        last_date = Date.now();
        $scope.last_refresh = Date.now();
        $timeout(updateUI, 1000);
    }

    var cancelNextLoad = function() {
        $timeout.cancel(loadPromise);
    };

    var nextLoad = function(mill) {
        mill = mill || loadTime;
        cancelNextLoad();
        loadPromise = $timeout(getPlayers, mill);
    };

    getPlayers();
    $scope.numplayers = '0 players';
    $scope.players = [];
    updateUI();
    
    $scope.$on('$destroy', function() {
        cancelNextLoad();
    });
});