/* global bubble_config, gradient_text */
'use strict';

var GameRootId = 'game_root';
var DMK_URL = 'http://localhost:8080/buibui/get_danmakus';

var SWIDTH = 1920;
var SHEIGHT = 1080; 

var game = new Phaser.Game(SWIDTH, SHEIGHT, Phaser.ATUO, GameRootId, null, true);

var blackBorderStyle = {
    strokeThickness: 2,
    stroke: '#000000',
};

var whiteBorderStyle = {
    strokeThickness: 2,
    stroke: '#FFFFFF',
};

var playState = (function() {
  var D_MODE_RIGHT2LEFT = 0;
  var D_MODE_LEFT2RIGHT = 1;
  var D_MODE_TOP = 2;
  var D_MODE_BOTTOM = 3;

  var POLLING_PERIOD = 1;

  var HORIZONTAL_PADDING = 20;

  var FONT_SIZE_MAP = {
    1: 0.03,
    2: 0.06,
    3: 0.1,
    4: 0.15,
  };
  
  var DANMAKU_TTL = 10000;

  var AllocatorLayer = function(type, offset) {
    this.type = type;
    this.offset = offset;
    this.pool = [];
  };

  AllocatorLayer.prototype = {
    allocte: function(dmk) {
      var base_line = this.get_slots();
      var y = this.offset;
      for(var k in base_line) {
        var i = base_line[k]; 
        if(i.y > y && i.y > dmk.height + y) {
          dmk.y = y;
          this.pool.push(dmk);
          return true;
        }
        y = i.y + i.height + 1;
      }
      return false;
    },

    free: function(dmk) {
      var index = this.pool.indexOf(dmk);
      if(index == -1) {
        return false;
      }
      this.pool.splice(index, 1);
      dmk.destroy();
      return true; 
    },

    get_slots: function() {
      if(this.type == D_MODE_RIGHT2LEFT) {
        var base_line = this.pool.filter(function(i) {
          return i.width + i.x + HORIZONTAL_PADDING > SWIDTH;
        });
        base_line.push({y: SHEIGHT, height: 0});
        return base_line.sort(function(a, b){a.y - b.y});
      }
      if(this.type == D_MODE_LEFT2RIGHT) {
        var base_line = this.pool.filter(function(i) {
          return i.x - HORIZONTAL_PADDING < 0;
        });
        base_line.push({y: SHEIGHT, height: 0});
        return base_line.sort(function(a, b){a.y - b.y});
      }
      if(this.type == D_MODE_TOP) {
        var base_line = this.pool.filter(function() { return true});
        base_line.push({y: SHEIGHT, height: 0});
        return base_line.sort(function(a, b){a.y - b.y});
      }
    },
  };
  
  var AllocatorLayerBottom = function(offset) {
    this.offset = offset;
    this.pool = [];
  };

  AllocatorLayerBottom.prototype = {
    allocte: function(dmk) {
      var base_line = this.get_slots()
      var y = SHEIGHT - dmk.height - this.offset;
      for(var k in base_line) {
        var i = base_line[k]; 
        if(i.y + i.height < y && i.y < y) {
          dmk.y = y;
          this.pool.push(dmk);
          return true;
        }
        y = i.y - dmk.height - 1;
      }
      return false;
    },

    free: function(dmk) {
      var index = this.pool.indexOf(dmk);
      if(index == -1) {
        return false;
      }
      this.pool.splice(index, 1);
      dmk.destroy();
      return true; 
    },

    get_slots: function() {
      var base_line = this.pool.filter(function() { return true});
      base_line.push({y: 0, height: 0});
      return base_line.sort(function(a, b){b.y - a.y});
    },
  };

  var Allocator = function(layer_type) {
    this.layers = {};
    this.layer_type = layer_type;
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
      if(this.layer_type == D_MODE_BOTTOM) {
        this.layers[idx] = new AllocatorLayerBottom(offset);
      }else {
        this.layers[idx] = new AllocatorLayer(this.layer_type, offset);
      }
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
  
  var get_ts = function() {
    var ts_obj = new Date();
    return Math.floor(ts_obj.getTime());
  };

  return {
    preload: function(){
      game.stage.disableVisibilityChange = true;
      game.scale.maxWidth = 1920;
      game.scale.maxHeight = 1080;

      game.scale.scaleMode = Phaser.ScaleManager.SHOW_ALL;
      game.scale.setScreenSize();
    },

    init: function() {
      this.last_time = get_ts();
      this.alloctors = {
        0: new Allocator(0),
        1: new Allocator(1),
        2: new Allocator(2),
        3: new Allocator(3),
      };
    },
    
    create: function() {
      this.round_timer = game.time.events.add(Phaser.Timer.SECOND, this.tick, this);
    },
    
    tick: function() {
      var _this = this;
      this.pull_msgs(function(msgs) {
        msgs.forEach(function(i) {
          _this.danmaku_builder(i);
        });
      });
    },
    
    pull_msgs: function(cb) {
      var _this = this;
      $.ajax({
        url: DMK_URL, 
        data: {ts: _this.last_time}, 
        type: 'GET',
        dataType: 'json',
        success: function(data) {
          var msgs = data.danmakus;
          msgs = msgs.sort(function(a, b) { a.ts - b.ts; });
          if(msgs.length > 0) {
            _this.last_time = msgs[msgs.length - 1].ts
          }
          _this.round_timer = game.time.events.add(Phaser.Timer.SECOND, _this.tick, _this);
          cb(msgs);
        },
        error: function() {
          _this.round_timer = game.time.events.add(Phaser.Timer.SECOND, _this.tick, _this);
        },
      });
    },
    
    danmaku_builder: function(msg) {
      var borderStyle;
      if (msg.color === '#FFFFFF') {
          borderStyle = blackBorderStyle;
      } else {
          borderStyle = whiteBorderStyle
      }

      var text = game.add.text(0, 0, msg.text, borderStyle);
      text.anchor.set(0);
      text.align = 'left';

      text.fontSize = Math.floor(FONT_SIZE_MAP[msg.size] * SHEIGHT);
      text.fill = msg.color;
      
      var mode = msg.mode;
      var alloctor = this.alloctors[mode];
      alloctor.allocte(text);
      
      if(mode == D_MODE_RIGHT2LEFT){
        text.x = SWIDTH;
        var tween = game.add.tween(text).to({x: -text.width}, DANMAKU_TTL, null, true);
        tween.onComplete.add(alloctor.free, alloctor, text);
      }else if(mode == D_MODE_LEFT2RIGHT){
        text.x = -text.width;
        var tween = game.add.tween(text).to({x: SWIDTH}, DANMAKU_TTL, null, true);
        tween.onComplete.add(alloctor.free, alloctor, text);
      }else if(mode == D_MODE_TOP){
        text.x = Math.floor((SWIDTH - text.width)/2); 
        game.time.events.add(Phaser.Timer.SECOND * 5, function(){
          alloctor.free(text)
        });
      }else if(mode == D_MODE_BOTTOM){
        text.x = Math.floor((SWIDTH - text.width)/2); 
        game.time.events.add(Phaser.Timer.SECOND * 5, function(){
          alloctor.free(text)
        });
      }
      return text;
    },
  };
})();

game.state.add('play', playState);
game.state.start('play');
