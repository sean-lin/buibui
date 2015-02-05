/* global bubble_config, gradient_text */
'use strict';

var GameRootId = 'game_root';
var DMK_URL = 'http://localhost:8080/buibui/get_danmakus?ts=';

var SWIDTH = 800;
var SHEIGHT = 600;

var game = new Phaser.Game(SWIDTH, SHEIGHT, Phaser.ATUO, GameRootId, null, true);

game.state.add('play', playState);
game.state.start('play');

var playState = (function() {
  var D_MODE_RIGHT2LEFT = 0;
  var D_MODE_LEFT2RIGHT = 1;
  var D_MODE_TOP = 2;
  var D_MODE_BOTTOM = 3;

  var POLLING_PERIOD = 1;

  var HORIZONTAL_PADDING = 20;

  var FONT_SIZE_MAP = {
    1: 0.05,
    2: 0.1,
    3: 0.15,
    4: 0.2,
  };

  var AllocatorLayer = function(offset) {
    this.offset = offset;
    this.pool = [];
  };

  AllocatorLayer.prototype = {
    allocte: function(dmk) {
      var base_line = this.get_slots()
      var y = this.offset;
      for(var i in base_line) {
        if(i.y > y && i.y > dmk.height + y) {
          dmk.y = y;
          this.pool.push(dmk);
          return true;
        }
      }
      return false;
    },

    free: function(dmk) {
      var index = this.pool.indexOf(dmk);
      if(index == -1) {
        return false;
      }
      this.pool.splice(index, 1);
      return true; 
    },

    get_slots: function() {
      var base_line = self.pool.fillter(function(i) {
        return i.width + i.x + HORIZONTAL_PADDING > SWIDTH;
      });
      base_line.push({y: this.offset, height: 0});
      return base_line.sort(function(a, b){a.y - b.y});
    }
  };
 
  var Allocator = function(layer_cls) {
    this.layers = {};
    this.layer_cls = layer_cls;
  };

  Allocator.prototype = {
    allocte: function(dmk) {
      var idx = 0;
      for(var i in this.layers){
        if(this.layers[i].allocte(dmk)) {
          return;
        }
        idx +=1;
      }
      var offset = this.gen_offset(idx);
      this.layers[idx] = new this.layer_cls(offset);
      this.layers[idx].allocte(dmk);
    },

    free: function(dmk) {
      for(var i in this.layers) {
        if(this.layers[i].free(dmk)){
          return true;
        }
      }
      return false;
    },

    gen_offset: function(idx) {
      return idx * 15 % SHEIGHT;
    },
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
