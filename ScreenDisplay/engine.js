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

    }, opts || {}),
    // This is the actual breakdown of the content on
    // the screen into different partitions
    _box = {},
    _last = false,
    _uniq = 0,
    _last_uniq = false,
    _last_container = false,
    _current = false,
    _playCount = 0,
    _job_id = 0,
    _downweight = 0.7,
    _firstRun = false,
    _nop = function(){},
    _isNetUp = true,
    _start = new Date(),
    _stHandleMap = {},
    _key = '-xA8tAY4YSBmn2RTQqnnXXw',
    _last_sow = [+_start, +_start],
    _ = {
      maxPriority: 0,
    },
    _fallback;

  if(_res.dynamicSize) {
    _res.target.width = _res.container.clientWidth;
    _res.target.height = _res.container.clientHeight;
  }

  _res.target.ratio = _res.target.width / _res.target.height;

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

    mostRecent: function() {
      if(Timeline._data.length > 1) {
        var last = (Timeline.position + Timeline._data.length - 1) % Timeline._data.length;
        return Timeline._data[last];
      }
    },

    addAtEnd: function(job) {
      Timeline._data.push(job);
      Timeline.bath();
    },
  };

  function layout() {
    //
    // <div class=top>
    //   <div class=widget></div>
    //   <div class=ad></div>
    // </div>
    // <div class=bottom>
    //   <div class=time></div>
    //   <div class=ticker></div>
    // </div>
    //
    ["top","ad","widget","bottom","time","ticker"].forEach(function(row) {
      _box[row] = document.createElement("div");
      _box[row].className = row;
    });
    // this ordering is correct...trust me.
    _box.top.appendChild(_box.widget);
    _box.top.appendChild(_box.ad);
    _box.bottom.appendChild(_box.time);
    _box.bottom.appendChild(_box.ticker);
    _res.container.appendChild(_box.top);
    _res.container.appendChild(_box.bottom);
    _res.container.classList.add('engine' + _key);
  }

  function cleanTimeout(what, dur) {
    return setTimeout(function() { 
      what();
    }, dur);
  }

  function isString(obj) { 
    return !!(obj === '' || (obj && obj.charCodeAt && obj.substr));
  }

  function event(what, data) {
    //console.log('>> trigger ' + what);
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
        e.target.style.width = '100%';
        /*
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
        */
      }
      asset.active = true;
      obj.active = true;
    }
    img.src = asset.url;

    asset.active = true;
    // TODO: per asset custom duration 
    asset.duration = asset.duration || _res.duration;
    obj.duration += asset.duration;
    asset.pause = asset.run = asset.play = _nop;
    asset.dom = img;

    return asset;
  }

  function iframe(asset, obj) {
    var dom = document.createElement('iframe');
    dom.src = asset.url;
    asset.dom = dom;
    asset.pause = asset.play = _nop;
    asset.run = function() {
      _playCount ++;
    }
    asset.active = true;
    asset.duration = asset.duration || 100 * _res.duration;
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

    asset.cycles = 1;
    asset.pause = vid.pause;
    asset.play = vid.play;
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
      if(!asset.duration) {
        asset.duration = vid.duration;
      } else {
        asset.duration = Math.min(vid.duration, asset.duration);
      }
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
    if(asset.mime) { 
      return asset.mime.match(mime);
    }
    if(asset.type) { 
      return asset.type.match(mime);
    }
    return asset.url.match('(' + ext.join('|') + ')');
  }

  function urlToAsset(url, obj) {
    var container = document.createElement('div');
    var asset = isString(url) ? {url: url} : url;
    container.classList.add('container' + _key);

    if(assetTest(asset, 'image', ['png','jpg','jpeg'])) {
      asset = image(asset, obj);
    } else if(assetTest(asset, 'video', ['mp4', 'avi', 'mov', 'ogv'])) {
      asset = video(asset, obj);
    } else {
      asset = iframe(asset, obj);
    }
    asset.uniq = _uniq++;
    asset.container = container;
    asset.container.appendChild(asset.dom);
    return asset;
  }

  // All the things returned from this have 2 properties
  // 
  //  run() - for videos it resets the time and starts the video
  //  duration - how long the asset should be displayed.
  //
  function makeJob(obj) {
    obj = merge({
      downweight: 1,
      completed_seconds: 0,
      // We need multi-asset support on a per-job
      // basis which means we need to be able
      // to track
      position: 0,
      // This is the total duration of all the
      // assets included in this job.
      duration: 0,
      assetList: [],
      id: _job_id++,
    }, obj);
    
    if( ! ('url' in obj) && ('asset' in obj) ) {
      obj.url = obj.asset;
    }

    if( isString(obj.url) ) {
      obj.url = [ obj.url ];
    }

    if( obj.url ) {
      obj.assetList = obj.url.map(function(row) { return urlToAsset(row, obj); });
    }

    obj.remove = function(what) {
      obj.assetList = obj.assetList.filter(function(row) { return row.uniq != what.uniq });
      obj.duration = obj.assetList.reduce(function(a,b) { return a + b.duration }, 0);
    }

    obj.append = function(what) {
      var asset = urlToAsset(what, obj);
      obj.assetList.push(asset);
      return asset;
    }
        
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
      remote.ix++;
      return;
    }

    post('sow', payload, function(res) {
      if(res.res) {
        _res.db = {};
        res.data.forEach(function(row) {
          addJob(row);
        })
      }
      if(cb) {
        cb();
      }
    });
  }

  var Widget = {
    doTime: function() {
      var now = new Date();
      _box.time.innerHTML = [
          (now.getHours() + 100).toString().slice(1),
          (now.getMinutes() + 100).toString().slice(1)
        ].join(':')
    },
    active: {},
    show: {
      weather: function(cloud, temp) {
        _box.widget.innerHTML = [
          "<div class='app weather cloudy'>", 
          "<img src=cloudy_" + cloud + ".svg>",
          temp + "&deg;",
          "</div>"
        ].join('');
      }
    },
    updateView: function(what, where) {
      Widget.active[what] = where;
      var hasBottom = Widget.active.time || Widget.active.ticker;
      var hasWidget = hasBottom || Widget.active.app;
      _res.container.classList[hasWidget ? 'add' : 'remove']('addon');
      _res.container.classList[hasBottom ? 'add' : 'remove']('hasBottom');
    },

    time: function(onoff) {
      Widget.updateView('time', onoff);
      if(onoff) {
        _box.time.style.display = 'block';
        if(!Widget._time) {
          Widget._time = setInterval(Widget.doTime, 1000);
          Widget.doTime();
        }
      } else {
        _box.time.style.display = 'none';
        clearInterval(Widget._time);
        Widget._time = false;
      }
    },
    app: function(feed) {
      if(arguments.length === 0) {
        return;
      }
      Widget.updateView('app', feed);
      if(feed) {
        _box.widget.style.display = 'block';
        Widget.show.weather(50,72);
      } else {
        _box.widget.style.display = 'none';
      }
    },
    ticker: function(feed) {
      if(arguments.length === 0) {
        return;
      }
      Widget.updateView('ticker', feed);
      if(feed) {
        if(!Widget._ticker) {
          _box.ticker.style.display = 'block';
          function scroll() {
            _box.ticker.style.opacity = 1;
            _box.ticker.scrollLeft = 1;
            clearInterval(Widget._ticker);
            Widget._ticker = setInterval(function(){
              var before = _box.ticker.scrollLeft;
              _box.ticker.scrollLeft += 1.4
              if (_box.ticker.scrollLeft === before) {
                clearInterval(Widget._ticker);
                scroll();
              }
            }, 30);
          }

          _box.ticker.innerHTML = `
          <span>Saudi oil attacks: all the latest updates</span>
          <span>'Dollar diplomacy' - Taiwan condemns China after Solomons switch</span>`;
          scroll();
        }
      } else {
        _box.ticker.style.display = 'none';
        clearInterval(Widget._ticker);
        Widget._ticker = false;
      }
    },
  };

  function _timeout(fn, timeout, name, override) {
    var handle = override ? fn : setTimeout(fn, timeout);
    _stHandleMap[name] = {
      ts: new Date(), 
      handle: handle,
      timeout: timeout
    };
    return handle;
  }

  function clearAllTimeouts() {
    for(var name in _stHandleMap) {
      clearTimeout(_stHandleMap[name].handle);
      delete _stHandleMap[name];
    }
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
    var prev;
    var doFade = false;

    if(_res.pause) {
      return;
    }
    // If we are at the start of our job
    // then this is the only valid time we'd
    // be transitioning away from a previous job
    //
    // so this is when we do the reporting.
    if(_current.position === 0) {

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

        if(_last.job_id !== _current.job_id) {
          // we reset the downweight -- it can come back
          _last.downweight = 1;
        }
      }
    }

    // If we are at the end then our next function should be to
    // choose the next job.
    if(_current.position === _current.assetList.length) {
      event('jobEnded', _current);
      return nextJob();
    } 

    _current.shown = _current.assetList[_current.position];
    _current.shown.run();
    _box.ad.appendChild(_current.shown.container);

    if(_current.shown.uniq != _last_uniq) {
      // This is NEEDED because by the time 
      // we come back around, _last.shown will be 
      // redefined.
      prev = _last_container;
      if(prev) {
        prev.classList.add('fadeOut' + _key);
        _timeout(function() {
          prev.classList.remove('fadeOut' + _key);
          _box.ad.removeChild(prev);
        }, _res.fadeMs, 'assetFade');
        doFade = true;
      }
    }
    _last_uniq = _current.shown.uniq;
    _last_container = _current.shown.container;

    _current.shown.container.classList[doFade ? 'add' : 'remove' ]('fadeIn' + _key );

    //console.log(new Date() - _start, _playCount, "Job #" + _current.id, "Asset #" + _current.position, "Duration " + _current.shown.duration, _current.shown.url, _current.shown.cycles);

    // These will EQUAL each other EXCEPT when the position is 0.
    _last = _current;

    // And we increment the position to show the next asset
    // when we come back around
    _current.position ++;

    _timeout(nextAsset, Math.max(_current.shown.duration * 1000 - _res.fadeMs / 2, 1000), 'nextAsset');
  }

  function setNextJob(job) {
    _current = job;
    _current.downweight *= _downweight;
    _current.position = 0;
    //console.log(new Date() - _start, "Showing " + _current.id + " duration " + _current.duration);
    //
    // We set the start time of the showing of this ad
    // so we can cross-correlate the gps from the ScreenDaemon
    // when we send it off upstream.  We use the system time
    // which is consistent between the two time stores.
    _last_sow[0] = _last_sow[1];
    _last_sow[1] = +new Date();
    return job;
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

    _.maxPriority = Math.max.apply(0, Object.values(_res.db).map(row => row.priority || 0));

    var 
      activeList = Object.values(_res.db).filter(row => row.active && row.duration),// && row.filter === maxPriority),

      // Here's the range of numbers, calculated by looking at all the remaining things we have to satisfy
      range = activeList.reduce( (a,b) => a + b.downweight * (b.goal - b.completed_seconds), 0),

      row, accum = 0,
      // We do this "dice roll" to see 
      breakpoint = Math.random() * range;

    if(_res._debug) {
      console.log({active: activeList, db:_res.db, range: range, priority: _.maxPriority});
    }
    // If there's nothing we have to show then we fallback to our default asset
    if( range <= 0 ) {
      if(_res.server && _res._debug) {
        console.log("Range < 0, using fallback");
      }

      if(!_fallback) {
        // woops what do we do now?! 
        // I guess we just try this again?!
        return _timeout(nextJob, 1500, 'nextJob');
      }

      setNextJob(_fallback);

      if(!_firstRun && activeList.length == 0 && Object.values(_res.db) > 1) {
        // If we just haven't loaded the assets then
        // we can cut the duration down
        setAssetDuration(_current, 0, 0.2);
      } else {
        // Otherwise we have satisfied everything and
        // maybe just can't contact the server ... push
        // this out to some significant number
        setAssetDuration(_current, 0, _res.duration);
      }

    } else {
      // This is needed for the end case.
      _firstRun = true;
      _current = false;
      for(row of activeList) {

        accum += row.downweight * (row.goal - row.completed_seconds);
        if(accum > breakpoint) {
          setNextJob(row);
          break;
        }
      }
      if(!_current) {
        setNextJob(row);
      }
    }

    nextAsset();
  }

  function setFallback (url, force) {
    // We look for a system default
    if(force || (!_res.fallback && !url)) {
      // If we have a server we can get it from there
      get('/default', function(res) {
        _fallback = makeJob(res.data.campaign);
        _res.system = res.data.system;
        event('system', _res.system);
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

  // This makes sure the _box references are valid before
  // running Start().
  layout();

  // The convention we'll be using is that
  // variables start with lower case letters,
  // function start with upper case.
  return merge(_res, {
    Get: function(what) {
      return _[what];
    },
    Play: function() {
      _res.pause = false;
      if(_current) {
        _current.shown.play();
        nextAsset();
      } else {
        nextJob();
      }
    },
    Pause: function() {
      _res.pause = !_res.pause;
      console.log("Clearing setTimeout for the next asset");
      clearTimeout(_stHandleMap.nextAsset.handle);
      _current.shown.pause();
    },

    PlayNow: function(job, doNotModify) {
      // clear any pending timers
      clearAllTimeouts();

      // we set all the assets to active in the job regardless
      // of whether they've loaded or not.
      if(!doNotModify) {
        job.assetList.forEach(function(asset) {
          asset.active = true;
          asset.duration = 16;
        });
        job.active = true;
        job.duration = 16 * job.assetList.length;
      }

      // set it as the next thing to do
      setNextJob(job);

      // and display it.
      nextAsset();
    },

    Debug: function() {
      _res._debug = true;
      return {
        current: _current,
        last: _last,
        isNetUp: _isNetUp,
        box: _box
      };
    }, 
    Scrub: function(relative_time) {
      if(relative_time < 0) {
      }
    },
    Start: function(){
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
    Widget: Widget,
    SetFallback: setFallback,
    AddJob: function(obj, params) {
      var job;

      if(isString(obj)) {
        obj = {url: obj};
      }

      job = makeJob(obj || {});
      // this allows someone to set say,
      // the priority to a high number
      _res.db[job.id] = merge(job, params);
      return _res.db[job.id];
    }
  });
};

Engine.all = function(what) {
  Engine.list.forEach(function(row) {
    row[what]();
  });
}

Engine.list = [];
