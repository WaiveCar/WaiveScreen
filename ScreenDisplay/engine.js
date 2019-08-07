// This code, written in 2019, is designed to run on say, I dunno, IE 10 or so (2012)
// so ES6/ECMA2015 things are off the table for now. A few modern things are ok, 
// like Array.forEach, dom.classList, etc, but things like {[a]: 1, ...b} are probably not.
//
// If you're reading this and it's like 2022 or something, then go ahead and reconsider it,
// it'll probably be fine by then.
//
// Also it's worth noting that the instagram ad basically discards any notion of compatibility
// and uses css animations, css calc, the vw/vh units and a bunch of other fancy modern css3 
// stuff - doing that with a bunch of javascript setIntervals was a waste of time ... I really
// don't care that much - people will be viewing that on a smartphone and those usually aren't
// crufty old crap browsers.


// 2 mutually exclusive ways to timeline:
//
// be stupid and have the timeline feed the next job - this makes scrubbing hard
//   * Any scrubbing solution will involve moving an offset around a datastructure with
//     computed timestamps ... that makes it a timeline.
//
// be entirely timeline based and have the next job put something on the timeline - this creates latency problems.
//   * A "discard future" option will fix the latency issue
//
var Engine = function(opts){
  // Support {

  // Edge 12 FF 34 (2015)
  var merge = Object.assign || function (a,b) {
    for(var k in b) {
      a[k] = b[k];
    }
    return a;
  }
  // } End of support.


  var 
    _res = merge({
      // This is what the ads attach to
      container: document.body,

      // If a server is set, then the progress gets posted
      // off to it - also new assets and jobs can come from it.
      server: false,

      db: {},

      duration: 7.5,

      // This needs to more or less correspond to the CSS
      // animation delay in the engine.css file. There's
      // really complicated ways to edit it dynamically 
      // but no thanks.
      fadeMs: 500,

      pause: false,

      target: { width: 1920, height: 675 },

      listeners: {},
      data: {},

      _debug: false,
      _current: false

    }, opts || {}),
    _last = false,
    _playCount = 0,
    _id = 0,
    _downweight = 0.7,
    _firstRun = false,
    _nop = function(){},
    _isNetUp = true,
    _start = new Date(),
    _stHandleMap = {},
    _last_sow = [+_start, +_start],
    _fallback;

  _res.target.ratio = _res.target.width / _res.target.height;

  function cleanTimeout(what, dur) {
    return setTimeout(function() { 
      what();
    }, dur);
  }

  function isString(obj) { 
    return !!(obj === '' || (obj && obj.charCodeAt && obj.substr));
  }

  function trigger(what, data) {
    console.log('>> trigger ' + what);
    _res.data[what] = data;
    if(_res.listeners[what]) {
      _res.listeners[what].forEach(function(cb) {
        cb(data);
      });
    }
  }

  function assetError(obj, e) {
    // TODO we need to report an improperly loading
    // asset to our servers somehow so we can remedy
    // the situation.
    obj.active = false;
    console.log("Making " + obj.url + " inactive");
  }

  function image(asset, obj) {
    var img = document.createElement('img');
    img.onerror = function(e) {
      assetError(asset, e);
    }
    img.onload = function(e) {
      if(e.target.width) {
        var ratio = e.target.width / e.target.height;
        if(ratio > _res.target.ratio) {
          var maxHeight = _res.target.width * e.target.height / e.target.width;
          e.target.style.height =  Math.min(_res.target.height, maxHeight * 1.2) + "px";
          e.target.style.width = _res.target.width + "px";
          //console.log(_res.target.width, e.target.height, e.target.width, e.target.src);
        } else { 
          var maxWidth = _res.target.height * e.target.width / e.target.height;
          e.target.style.width =  Math.min(_res.target.width, maxWidth * 1.2) + "px";
          e.target.style.height = _res.target.height + "px";
        }
      }
      asset.active = true;
      obj.active = true;
    }
    img.src = asset.url;

    asset.active = true;
    // TODO: per asset custom duration 
    asset.duration = asset.duration || _res.duration;
    obj.duration += asset.duration;
    asset.run = _nop;
    asset.dom = img;

    return asset;
  }

  function iframe(asset, obj) {
    var dom = document.createElement('iframe');
    dom.src = asset.url;
    asset.dom = dom;
    asset.run = function() {
      _playCount ++;
    }
    asset.active = true;
    asset.duration = asset.duration || _res.duration;
    obj.duration += asset.duration;
    obj.active = true;
    return asset;
  }
  
  function video(asset, obj) {
    var vid = document.createElement('video');
    var src = document.createElement('source');

    vid.setAttribute('muted', true);
    //vid.setAttribute('preload', 'auto');
    vid.appendChild(src);

    src.src = asset.url;
    asset.dom = vid;

    // This was to avoid some weird flashing bug
    // before the videos loaded. However, there
    // should be a way to do overrides. So this
    // solution is insufficient
    asset.duration = asset.duration || 100;
    asset.cycles = 1;
    asset.run = function(noreset) {
      if(!noreset) {
        vid.currentTime = 0;
      }
      vid.volume = 0;
      var now = new Date();
      var playPromise = vid.play();

      if (playPromise !== undefined) {
        playPromise.then(function(e) {
          //console.log(new Date() - _start, count, asset.url + " promise succeeded", e);
        })
        .catch(function(e) {
          // console.log(new Date() - now);
          // console.log(new Date() - _start, "setting " + asset.url + " to unplayable", e);
          console.log(e.message, e.name);
          if(new Date() - now < 100) {
            // if we were interrupted in some normal interval, maybe it will just work
            // if we try again ... might as well - don't reset the clock though.
            //asset.run(true);
          }
          //asset.active = false;
        });
      }
      _playCount ++;
    }

    vid.ondurationchange = function(e) {
      // This will only come if things are playable.
      let vid = e.target;
      // This is probably wrong since we are making a decision this
      // far down the line.  Essentially what I want to do is allow
      // for a partial video to show if it's really long but also
      // be smart enough to show a short video smoothly.  It also
      // doesn't sound like something that can be done with such
      // little logic since there's ultimately an "opinion" here
      // of a threshold which means that it requires a numerical value
      // whose existence is clearly mysteriously absent. Ah, we'll
      // figure it out later, like most things in life.
      asset.duration = Math.min(vid.duration, asset.duration);
      asset.active = true;
      // if a video is really short then we force loop it.
      if(asset.duration < 0.8) {
        asset.cycles = Math.ceil(1/asset.duration); 
        vid.setAttribute('loop', true);
        console.log(asset.url + " is " + asset.duration + "s. Looping " + asset.cycles + " times");
        asset.duration *= asset.cycles;
      }
      vid.muted = true;
      if(vid.videoWidth) {
        var ratio = vid.videoWidth / vid.videoHeight;
        if(ratio > _res.target.ratio) {
          var maxHeight = _res.target.width * vid.videoHeight / vid.videoWidth;
          vid.style.height =  Math.min(_res.target.height, maxHeight * 1.2) + "px";
          vid.style.width = _res.target.width + "px";
        } else { 
          var maxWidth = _res.target.height * vid.videoWidth / vid.videoHeight;
          vid.style.width =  Math.min(_res.target.width, maxWidth * 1.2) + "px";
          vid.style.height = _res.target.height + "px";
        }
      } 
      obj.duration += asset.duration;
      obj.active = true;
    }

    // notice this is on the src assetect and not the vid
    // containers.
    src.onerror = function(e) {
      assetError(asset, e);
    }

    return asset;
  }
    
  function assetTest(asset, mime, ext) {
    return (asset.mime && asset.mime.match('/' + mime + '/')) || 
      (!asset.mime && asset.match('/(' + ext.join('|') + ')/'));
  }

  // All the things returned from this have 2 properties
  // 
  //  run() - for videos it resets the time and starts the video
  //  duration - how long the asset should be displayed.
  //
  function makeJob(obj) {
    obj.downweight = obj.downweight || 1;
    obj.completed_seconds = obj.completed_seconds || 0;
    // obj.what = obj.what || obj.url;
    
    // We need multi-asset support on a per-job
    // basis which means we need to be able
    // to track
    obj.position = 0;

    // This is the total duration of all the
    // assets included in this job.
    obj.duration = 0;

    obj.id = obj.id || (_id ++);
    //
    // We don't want to manually set this.
    // obj.goal
    //
    if( ! ('url' in obj) ) {
      obj.url = obj.asset;
    }

    if( isString(obj.url) ) {
      obj.url = [ obj.url ];
    }

    obj.assetList = obj.url.map(function(asset) {
      var container = document.createElement('div');
      container.classList.add('container');

      if(assetTest(asset, 'image', ['png','jpg','jpeg'])) {
        asset = image(asset, obj);
      } else if(assetTest(asset, 'video', ['mp4', 'avi', 'mov', 'ogv'])) {
        asset = video(asset, obj);
      } else {
        asset = iframe(asset, obj);
      }
      asset.container = container;
      asset.container.appendChild(asset.dom);
      return asset;
    });
        
    return obj;
  }

  function scroll(obj, dim) {
    var 
      size     = dim == 'vertical' ? _res.target.height : _res.target.width,
      anchor   = dim == 'vertical' ? 'marginTop' : 'marginLeft',
      goal = obj[dim == 'vertical' ? 'height' : 'width'] - size,
      time = _res.duration * 1000,
      period = 1000 / 30,
      rounds = time / period,
      step = goal / rounds,
      ix = 0,
      ival = setInterval(function() {
        if (ix++ >= rounds) {
          clearInterval(ival);
        }
        obj.style[ anchor ] = -(ix * step) + "px";
      }, period);
  }
  scroll.vertical = function (obj) {
    return scroll(obj, 'vertical');
  }
  scroll.horizontal = function (obj) {
    return scroll(obj, 'horizontal');
  }

  // LRU cache invalidation should eventually exist.
  function addJob(job) {
    if(!_res.db[job.campaign_id]) {

      // This acts as the instantiation. 
      // the merging of the rest of the data
      // will come below.
      console.log(job.asset);
      _res.db[job.campaign_id] = makeJob({ url: job.asset });
    }

    // This places in things like the goal
    _res.db[job.campaign_id] = merge(
      _res.db[job.campaign_id], job
    );

    return _res.db[job.campaign_id];
  }

  // TODO: A circular buffer to try and navigate poor network
  // conditions.
  function remote(verb, url, what, onsuccess, onfail) {
    if(!_res.server) { return; }
    onfail = onfail || function(a){
      console.log(a);
    }
    if(!_res.server) {
      onfail();
    }
    remote.ix = (remote.ix + 1) % remote.size;

    if(remote.lock[url]) {
      console.log("Not connecting, locked on " + remote.lock[url]);
      return false;
    }
    // Try to avoid a barrage of requests
    remote.lock[url] = remote.ix;

    var http = new XMLHttpRequest();

    http.open(verb, _res.server + url.replace(/^\/*/,''), true);
    http.setRequestHeader('Content-type', 'application/json');

    http.onreadystatechange = function() {
      if(http.readyState == 4) {
        remote.lock[url] = false;
        if( http.status == 200) {
          _isNetUp = true;
          var res = JSON.parse(http.responseText);

          if(res.res === false) {
            onfail(res.data);
          } else {
            onsuccess(res);
          }
        } else if(http.status == 500 && onfail) {
          onfail();
        }
      }
    }

    http.onabort = http.onerror = http.ontimeout = function(){
      if(onfail) {
        onfail();
      }
      // ehhh ... maybe we just can't contact things?
      _isNetUp = false;
      remote.lock[url] = false;
    }
    
    if(what) {
      http.send(JSON.stringify(what));
    } else {
      http.send();
    }
  }
  remote.lock = {};

  function get(url, onsuccess, onfail) {
    return remote('GET', url, false, onsuccess, onfail);
  }
  function post(url, what, onsuccess, onfail) {
    return remote('POST', url, what, onsuccess, onfail);
  }
  remote.size = 5000;
  remote.ix = 0;

  function sow(payload, cb) {
    // no server is set
    if(!_res.server) {
      if(remote.ix == 0) {
        console.info("No server is set.");
      }
      remote.ix++;
      return;
    }

    post('sow', payload, function(res) {
      if(res.res) {
        res.data.forEach(function(row) {
          addJob(row);
        })
      }
      if(cb) {
        cb();
      }
    });
  }

  function setAssetDuration(what, index, amount) {
    // Update the total aggregate to reflect the new amount
    what.duration -= (what.duration - amount);

    // Now set the new amount
    what.assetList[index].duration = amount;
  }

  // Jobs have assets. nextJob chooses a job to run and then asks nextAsset
  // to do that work ... when nextAsset has no more assets for a particular job
  // it calls nextJob again.
  function nextAsset() {
    if(_res.pause) {
      return;
    }
    var prev;
    var doFade = false;
    // If we are at the start of our job
    // then this is the only valid time we'd
    // be transitioning away from a previous job
    //
    // so this is is when we do the reporting.
    if(_res.debug) {
      console.log(_res._current);
    }
    if(_res._current.position === 0) {

      // If this exists then it'd be set at the last asset
      // previous job.
      if(_last) {
        // We can state that we've shown all the assets that
        // we plan to show
        _last.completed_seconds += _last.duration;

        // and report it up to the server
        sow({
          start_time: _last_sow[0],
          end_time: _last_sow[1],
          job_id: _last.job_id,
          campaign_id: _last.campaign_id, 
          completed_seconds: _last.completed_seconds
        });

        if(_last.job_id !== _res._current.job_id) {
          // we reset the downweight -- it can come back
          _last.downweight = 1;
        }
      }
    }

    // If we are at the end then our next function should be to
    // choose the next job.
    if(_res._current.position === _res._current.assetList.length) {
      if(!_res.pause) {
        nextJob();
      }
    } else { 
      // ****
      // This ordering is important! 
      // ****
      //
      // We may (quite likely) will
      // have (_last === _res._current) most of the time. This means
      // that we are "passing the torch" of the .shown pointer,
      // being more than likely just one.
      if(_last && (_res._current.position > 0 || _last.id !== _res._current.id)) {
        //console.log(_res._current.position, _last.id, _res._current.id);
        _last.shown.container.classList.add('fadeOut');

        // This is NEEDED because by the time 
        // we come back around, _last.shown will be 
        // redefined.
        prev = _last.shown;
        _timeout(function() {
          prev.container.classList.remove('fadeOut');
          if(prev.container.parentNode) {
            prev.container.parentNode.removeChild(prev.container);
          } else {
            console.log("Not able to remove container");
          }
        }, _res.fadeMs, 'assetFade');
        doFade = true;
      }


      // Now we're ready to show the asset. This is done through
      // a pointer as follows:
      _res._current.shown = _res._current.assetList[_res._current.position];
      //console.log(new Date() - _start, _playCount, "Job #" + _res._current.id, "Asset #" + _res._current.position, "Duration " + _res._current.shown.duration, _res._current.shown.url, _res._current.shown.cycles);
      
      if(doFade) {
        _res._current.shown.container.classList.add('fadeIn');
      } else {
        _res._current.shown.container.classList.remove('fadeIn');
      }
      _res._current.shown.run();
      _res.container.appendChild(_res._current.shown.container);

      // And we increment the position to show the next asset
      // when we come back around
      _res._current.position ++;

      // These will EQUAL each other EXCEPT when the position is 0.
      _last = _res._current;

      if(!_res.pause) {
        _timeout(nextAsset, _res._current.shown.duration * 1000 - _res.fadeMs / 2, 'nextAsset');
      }
    }
  }

  var Timeline = {
    _data: [], 
    // This goes forward and loops around ... *almost*
    // it depends on what happens, see below for more
    // excitement.
    position: 0,

    // This returns if thre is a next slot without looping.
    hasNext: function() {
     return Timeline._data.length > Timeline.position;
    },

    // This is different, this will loop.
    move: function(amount) {
      // the classic trick for negatives
      Timeline.position = (Timeline._data.length + Timeline.position + amount) % Timeline._data.length
      return Timeline._data[Timeline.position];
    },

    bath: function() {
      // scrub scrub, clean up time.
      // This is actually only 3 hours of 7 second ads
      // which we cut back to 2. This should be fine 
      if(Timeline._data.length > 1500 && Timeline.position > 500) {
        // this moves our pointer
        Timeline._data = Timeline._data.slice(500);
        // so we move our pointer.
        Timeline.position -= 500;
      }
    },

    add: function(job) {
      // Just adds it to the current place.
      Timeline._data.splice(Timeline.position, 0, job);
      Timeline.bath();
    },

    addAtEnd: function(job) {
      Timeline._data.push(job);
      Timeline.bath();
    },
  }

  function _timeout(fn, timeout,  name, override) {
    var handle = override ? fn : setTimeout(fn, timeout);
    _stHandleMap[name] = {
      ts: new Date(), 
      handle: handle,
      timeout: timeout
    };
    return handle
  }

  function nextJob() {
    // We note something we call "breaks" which designate which asset to show.
    // This is a composite of what remains - this is two pass, eh, kill me.
    //
    // Also this heavily favors new jobs or pinpoint jobs in a linear distribution
    // which may be the "right" thing to do but it makes the product look a little 
    // bad.
    // 
    // We could sqrt() the game which would make the linear slant not look so crazy
    // but that's not the point ... the point is to change if we can.
    //
    // so what we do is "downweight" the previous by some compounding constant, defined
    // here by _downweight.
    //

    //
    // Essentially we populate some range of number where each ad occupies part of the range
    // Then we "toss a dice" and find what ad falls in the value we tossed.  For instance,
    //
    // Pretend we have 2 ads, we can make the following distribution:
    //
    // 0.0 - 0.2  ad 1
    // 0.2 - 1.0  ad 2
    //
    // In this model, a fair dice would show ad 2 80% of the time.
    //
    var 
      maxPriority = Math.max.apply(0, Object.values(_res.db).map(row => row.priority || 0)),
      activeList = Object.values(_res.db).filter(row => row.active),// && row.filter === maxPriority),

      // Here's the range of numbers, calculated by looking at all the remaining things we have to satisfy
      range = activeList.reduce( (a,b) => a + b.downweight * (b.goal - b.completed_seconds), 0),

      row, accum = 0,
      // We do this "dice roll" to see 
      breakpoint = Math.random() * range;

    if(_res._debug) {
      console.log({active: activeList, range: range, priority: maxPriority});
    }
    // If there's nothing we have to show then we fallback to our default asset
    if( range <= 0 ) {
      if(_res.server) {
        console.log("Range < 0, using fallback");
      }

      if(!_fallback) {
        // woops what do we do now?! 
        // I guess we just try this again?!
        return _timeout(nextJob, 1500, 'nextJob');
      }

      _res._current = _fallback;

      if(!_firstRun && activeList.length == 0 && Object.values(_res.db) > 1) {
        // If we just haven't loaded the assets then
        // we can cut the duration down
        setAssetDuration(_res._current, 0, 0.2);
      } else {
        // Otherwise we have satisfied everything and
        // maybe just can't contact the server ... push
        // this out to some significant number
        setAssetDuration(_res._current, 0, _res.duration);
      }

    } else {
      // This is needed for the end case.
      _firstRun = true;
      _res._current = false;
      for(row of activeList) {

        accum += row.downweight * (row.goal - row.completed_seconds);
        if(accum > breakpoint) {
          _res._current = row;
          break;
        }
      }
      if(!_res._current) {
        _res._current = row;
      }
    }

    // 
    // By this time we know what we plan on showing.
    //
    _res._current.downweight *= _downweight;
    _res._current.position = 0;
    //console.log(new Date() - _start, "Showing " + _res._current.id + " duration " + _res._current.duration);
    //
    // We set the start time of the showing of this ad
    // so we can cross-correlate the gps from the ScreenDaemon
    // when we send it off upstream.  We use the system time
    // which is consistent between the two time stores.
    _last_sow[0] = _last_sow[1];
    _last_sow[1] = +new Date();

    _timeout(nextAsset, 2000, 'nextAsset');
  }

  function setFallback (url, force) {
    // We look for a system default
    if(force || (!_res.fallback && !url)) {
      // If we have a server we can get it from there
      get('/default', function(res) {
        _fallback = makeJob(res.data.campaign);
        _res.system = res.data.system;
        trigger('system', _res.system);
        _timeout(function() {
          setFallback(false, true);
        }, 3 * 60 * 1000, 'setFallback');
      }, function() { 
        _timeout(cleanTimeout(setFallback, _res.duration * 1000), _res.duration * 1000, 'setFallback', true);
      });

    } else {
      _res.fallback = _res.fallback || url;
      _fallback = makeJob({url: _res.fallback, duration: .1});
    }
  }

  // A repository of engines
  Engine.list.push(_res);

  // The convention we'll be using is that
  // variables start with lower case letters,
  // function start with upper case.
  return merge(_res, {
    Play: function() {
      _res.pause = false;
      _res._current.shown.dom.play();
      nextAsset();
    },
    Pause: function() {
      _res.pause = !_res.pause;
      console.log("Clearing setTimeout for the next asset");
      clearTimeout(_stHandleMap.nextAsset.handle);
      _res._current.shown.dom.pause();
    },

    Debug: function() {
      return {
        current: _res._current,
        last: _last,
        isNetUp: _isNetUp 
      };
    }, 
    Scrub: function(relative_time) {
      if(relative_time < 0) {
      }
    },
    Start: function(){
      _res.container.classList.add('engine');
      // Try to initially contact the server
      sow();
      _res.SetFallback();
      nextJob();
    },
    on: function(what, cb) {
      console.log('>> on ' + what);
      if(_res.data[what]) {
        cb(_res.data[what]);
      } else { 
        if(!(what in _res.listeners)) {
          _res.listeners[what] = [];
        }
        _res.listeners[what].push(cb);
      }
    },
    SetFallback: setFallback,
    AddJob: function(obj) {
      var res = {};
      obj = makeJob(obj);
      _res.db[obj.id] = obj;
      res[obj.id] = obj;
      return res;
    }
  });
};

Engine.all = function(what) {
  Engine.list.forEach(function(row) {
    row[what]();
  });
}

Engine.list = [];
Engine.width = 1920;
Engine.height = 675;
Engine.ratio = Engine.width / Engine.height;
