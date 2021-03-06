var app = angular.module('toppmart', ['infinite-scroll']);
angular.module('infinite-scroll').value('THROTTLE_MILLISECONDS', 1000);

// replace curly braces with @@ (collides w/ rendering engine)
app.config(function($interpolateProvider) {
    $interpolateProvider.startSymbol('@@')
    $interpolateProvider.endSymbol('@@');
});

app.filter('dateFilter', ['$filter', function($filter) {
    return function(input) {
        d = input;
        var h = Math.floor(d / 3600);
        var m = Math.floor(d % 3600 / 60);
        var s = Math.floor(d % 3600 % 60);

        var hDisplay = h > 0 ? h + (h == 1 ? " hour " : " hours ") : "";
        var mDisplay = m > 0 ? m + (m == 1 ? " minute " : " minutes ") : "";
        var sDisplay = s > 0 ? s + (s == 1 ? " second" : " seconds") : "";
        return hDisplay + mDisplay + sDisplay;
    }
}]);

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
        $http.get('/sim/json/players')
        .then(function(res) {
          if (sidebar_id == null || sidebar_id != res.data.id) {
              if (res.data.players.length == 0) {
                   $scope.numPlayers = '0 players';
                   $scope.players = [];
              } else {
                  // Compute the ranks
                  var rank_list = res.data.players.concat(res.data.offline_players).sort((a, b) =>
                    (b.time  + (b.in_sim ? b.elapsed : 0)) - (a.time +  + (a.in_sim ? a.elapsed : 0))
                  );
                  var rank_dict = {};
                  for (var i = 0; i < rank_list.length; i++) {
                    rank_dict[rank_list[i].username] = i + 1;
                  }

                  for (var i = 0; i < res.data.players.length; i++) {
                      res.data.players[i].width = 100 * res.data.players[i].elapsed/res.data.max_time;
                      res.data.players[i].elapsed_formatted = format_time(res.data.players[i].elapsed);
                      var split_name = res.data.players[i].username.split(" ");
                      res.data.players[i].rank = rank_dict[res.data.players[i].username];
                      if (split_name.length > 0 && split_name[1] == "Resident") {
                          res.data.players[i].username = split_name[0];
                      }
                  }

                  for (var i = 0; i < res.data.offline_players.length; i++) {
                      res.data.offline_players[i].elapsed_formatted = format_time(res.data.offline_players[i].elapsed);
                      var split_name = res.data.offline_players[i].username.split(" ");
                      res.data.offline_players[i].rank = rank_dict[res.data.offline_players[i].username];
                      if (split_name.length > 0 && split_name[1] == "Resident") {
                          res.data.offline_players[i].username = split_name[0];
                      }
                  }

                  $scope.numPlayers = res.data.players.length + ' player' + (res.data.players.length > 1 ? 's' : '');
                  $scope.players = res.data.players.sort((b,a) => b.elapsed - a.elapsed);
                  $scope.offlinePlayers = res.data.offline_players.sort((b,a) => b.elapsed - a.elapsed);
                  $scope.offline = $scope.offlinePlayers.slice(0, $scope.numLoaded);
                  $scope.numOfflinePlayers = res.data.offline_players.length + ' player' + (res.data.offline_players.length > 1 ? 's' : '');
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

        for (var i = 0; i < players.length; i++) {
            players[i].elapsed += elapsed;
            players[i].width = 100 * players[i].elapsed/$scope.max_time;
            players[i].elapsed_formatted = format_time(players[i].elapsed);
        }

        offlinePlayers = $scope.offlinePlayers;

        for (var i = 0; i < offlinePlayers.length; i++) {
            offlinePlayers[i].elapsed += elapsed;
            offlinePlayers[i].elapsed_formatted = format_time(offlinePlayers[i].elapsed);
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
    $scope.numPlayers = '0 players';
    $scope.players = [];
    $scope.offline = [];
    $scope.numOfflinePlayers = '0 away';
    $scope.offlinePlayers = [];
    $scope.numLoaded = 9;

    $scope.loadMore = function() {
        if ($scope.numLoaded < $scope.offlinePlayers.length) {
            $scope.numLoaded = $scope.numLoaded + 120;
            $scope.offline = $scope.offlinePlayers.slice(0, $scope.numLoaded);
        }
    }

    updateUI();
    
    $scope.$on('$destroy', function() {
        cancelNextLoad();
    });
});
