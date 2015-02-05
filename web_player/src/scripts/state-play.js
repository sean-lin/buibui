/* global bubble_config, gradient_text */
'use strict';

var GameRootId = 'game_root';
var DMK_URL = 'http://localhost:8080/buibui/get_danmakus?ts=';

var game = new Phaser.Game(800, 600, Phaser.ATUO, GameRootId, null, true);

game.state.add('play', playState);
game.state.start('play');

var playState = (function() {
  var D_MODE_RIGHT2LEFT = 0;
  var D_MODE_LEFT2RIGHT = 1;
  var D_MODE_TOP = 2;
  var D_MODE_BOTTOM = 3;

  var POLLING_PERIOD = 1

  var Danmaku = function() {

  };
  Danmaku.prototype = {
  };

  var init = function() {
    this.last_time = this.get_ts();
  };

  var create = function() {
  };

  var update = function() {
    return ;
    var _this = this;
    var msgs = this.pull_msgs();
    msgs.forEach(function(i) {
      var dmk = this.danmaku_builder(msg);
      _this.allocte(msg)
    });
  };

  var get_ts = function() {
    var ts_obj = new Data();
    return ts_obj.getTime() / 1000
  };
 
  var danmaku_builder = function(msg) {
  };

  var pull_msgs = function() {
  }
  return {create: create, update: update, init: init};
})();
