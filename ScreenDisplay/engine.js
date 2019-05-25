// This code, written in 2019, is designed to run on say, I dunno, IE 10 or so (2012)
// so ES6/ECMA2015 things are off the table for now. A few modern things are ok, 
// like Array.forEach, dom.classList, etc, but things like {[a]: 1, ...b} are probably not.
//
// If you're reading this and it's like 2022 or something, then go ahead and reconsider it,
// it'll probably be fine by then.
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

  // Edge 14 FF 43 (2016)
  // Note: Not a true polyfill, this is just how I use it in practice.
  if(!Array.prototype.includes) {
    Object.defineProperty(Array.prototype, 'includes', {
      value: function(valueToFind) {
        return this.indexOf(valueToFind) !== -1;
      }
    });
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

      pause: false

    }, opts || {}),
    _current = false,
    _last = false,
    _playCount = 0,
    _id = 0,
    _downweight = 0.7,
    _firstRun = false,
    _nop = function(){},
    _isNetUp = true,
    _start = new Date(),
    _fallback;

  function isString(obj) { 
    return !!(obj === '' || (obj && obj.charCodeAt && obj.substr));
  }

  function assetError(obj, e) {
    // TODO we need to report an improperly loading
    // asset to our servers somehow so we can remedy
    // the situation.
    obj.active = false;
    console.log("Making " + obj.url + " inactive");
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
      asset.duration = asset.duration || e.target.duration;
      asset.active = true;
      // if a video is really short then we force loop it.
      if(asset.duration < 0.8) {
        asset.cycles = Math.ceil(1/asset.duration); 
        vid.setAttribute('loop', true);
        console.log(asset.url + " is " + asset.duration + "s. Looping " + asset.cycles + " times");
        asset.duration *= asset.cycles;
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

    obj.assetList = obj.url.map(function(url) {
      var asset = {url: url};
      var ext = url.split('.').pop();

      if(['mp4','ogv','mpeg','webm','flv','3gp','avi'].includes(ext.toLowerCase()) ) {
        asset = video(asset, obj);
      } else {

        var img = document.createElement('img');
        img.onerror = function(e) {
          assetError(asset, e);
        }
        img.onload = function() {
          obj.active = true;
          asset.active = true;
        }
        img.src = url;

        asset.active = true;
        // TODO: per asset custom duration 
        asset.duration = _res.duration;
        obj.duration += asset.duration;
        asset.run = _nop;
        asset.dom = img;
      }
      return asset;
    });
        
    return obj;
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
    if(!_res.server) {
      onfail();
    }
    remote.ix = (remote.ix + 1) % remote.size;

    if(remote.lock) {
      console.log("Not connecting, locked on " + remote.lock);
      return false;
    }
    // Try to avoid a barrage of requests
    remote.lock = remote.ix;

    var http = new XMLHttpRequest();

    http.open(verb, _res.server + url.replace(/^\/*/,''), true);
    http.setRequestHeader('Content-type', 'application/json');

    http.onreadystatechange = function() {
      if(http.readyState == 4) {
        remote.lock = false;
        if( http.status == 200) {
          _isNetUp = true;
          onsuccess(JSON.parse(http.responseText));
        }
      }
    }

    http.onabort = http.onerror = http.ontimeout = http.onloadend = function(){
      if(onfail) {
        onfail();
      }
      // ehhh ... maybe we just can't contact things?
      _isNetUp = false;
      remote.lock = false;
    }
    
    if(what) {
      http.send(JSON.stringify(what));
    } else {
      http.send();
    }
  }
  function get(url, onsuccess, onfail) {
    return remote('GET', url, false, onsuccess, onfail);
  }
  function post(url, what, onsuccess, onfail) {
    return remote('POST', url, what, onsuccess, onfail);
  }
  remote.size = 5000;
  remote.ix = 0;

  function sow(payload) {
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
    if(_current.position === 0) {
      // We set the start time of the showing of this ad
      // so we can cross-correlate the gps from the ScreenDaemon
      // when we send it off upstream.  We use the system time
      // which is consistent between the two time stores.
      _current.start_time = +new Date();

      // If this exists then it'd be set at the last asset
      // previous job.
      if(_last) {
        // We can state that we've shown all the assets that
        // we plan to show
        _last.completed_seconds += _last.duration;

        // and report it up to the server
        sow({
          start_time: _last.start_time,
          end_time: +new Date(),
          id: _last.id, 
          completed_seconds: _last.completed_seconds
        });

        if(_last.id !== _current.id) {
          // we reset the downweight -- it can come back
          _last.downweight = 1;
        }
      }
    }

    // If we are at the end then our next function should be to
    // choose the next job.
    if(_current.position === _current.assetList.length) {
      if(!_res.pause) {
        nextJob();
      }
    } else { 
      // ****
      // This ordering is important! 
      // ****
      //
      // We may (quite likely) will
      // have (_last === _current) most of the time. This means
      // that we are "passing the torch" of the .shown pointer,
      // being more than likely just one.
      if(_last && (_current.position > 0 || _last.id !== _current.id)) {
        console.log(_current.position, _last.id, _current.id);
        _last.shown.dom.classList.add('fadeOut');

        // This is NEEDED because by the time 
        // we come back around, _last.shown will be 
        // redefined.
        prev = _last.shown;
        setTimeout(function() {
          prev.dom.classList.remove('fadeOut');
          _res.container.removeChild(prev.dom);
        }, _res.fadeMs);
        doFade = true;
      }


      // Now we're ready to show the asset. This is done through
      // a pointer as follows:
      _current.shown = _current.assetList[_current.position];
      console.log(new Date() - _start, _playCount, "Job #" + _current.id, "Asset #" + _current.position, "Duration " + _current.shown.duration, _current.shown.url, _current.shown.cycles);
      
      if(doFade) {
        _current.shown.dom.classList.add('fadeIn');
      } else {
        _current.shown.dom.classList.remove('fadeIn');
      }
      _current.shown.run();
      _res.container.appendChild(_current.shown.dom);

      // And we increment the position to show the next asset
      // when we come back around
      _current.position ++;

      // These will EQUAL each other EXCEPT when the position is 0.
      _last = _current;

      if(!_res.pause) {
        setTimeout(nextAsset, _current.shown.duration * 1000 - _res.fadeMs / 2);
      }
    }
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
      activeList = Object.values(_res.db).filter(row => row.active),

      // Here's the range of numbers, calculated by looking at all the remaining things we have to satisfy
      range = activeList.reduce( (a,b) => a + b.downweight * (b.goal - b.completed_seconds), 0),

      row, accum = 0,
      // We do this "dice roll" to see 
      breakpoint = Math.random() * range;

    // If there's nothing we have to show then we fallback to our default asset
    if( range <= 0 ) {
      console.log("Range < 0, using fallback");

      if(!_fallback) {
        // woops what do we do now?! 
        // I guess we just try this again?!
        return setTimeout(nextJob, 1500);
      }

      _current = _fallback;

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
          _current = row;
          break;
        }
      }
      if(!_current) {
        _current = row;
      }
      console.log('>>>', _current);
    }

    // 
    // By this time we know what we plan on showing.
    //
    _current.downweight *= _downweight;
    _current.position = 0;
    //console.log(new Date() - _start, "Showing " + _current.id + " duration " + _current.duration);

    nextAsset();

  }

  function setFallback (url) {
    // We look for a system default
    if(!_res.fallback && !url) {
      function trylocal(){
        // For some unknown stupid fucked up completely mysterious reason
        // a local document when running locally and talking to local resources
        // can't have permission to access the local storage, you know, because
        // somehow that should be a more secure, less trusted context then 
        // running random fucking code from the wild internet. Unbelievable.
        //
        // Fuck google and fuck permissions.
        //
        var fuck_google;
        try {
          fuck_google = localStorage['default'];
        } catch (ex) { }

        if(fuck_google) {
          _fallback = makeJob(JSON.parse(fuck_google));
        } else if (_res.server) {
          // If we have a server defined and we have yet to succeed
          // to get our default then we should probably try it again
          // until we get it
          setTimeout(function(){setFallback()}, _res.duration * 1000);
        }
      }

      // If we have a server we can get it from there
      get('/default', function(res) {
        try {
          localStorage['default'] = JSON.stringify(res.data);
          trylocal();
        } catch (ex) { 
          _fallback = makeJob(res.data);
        }
      }, trylocal);

    } else {
      _res.fallback = _res.fallback || url;
      _fallback = makeJob({url: _res.fallback, duration: .1});
    }
  }

  // The convention we'll be using is that
  // variables start with lower case letters,
  // function start with upper case.
  return merge(_res, {
    Play: function() {
      _res.pause = false;
      _current.shown.dom.play();
      nextAsset();
    },
    Pause: function() {
      _res.pause = !_res.pause;
      _current.shown.dom.pause();
    },

    Debug: function() {
      return {
        current: _current,
        last: _last,
        isNetUp: _isNetUp 
      };
    }, 
    Start: function(){
      _res.container.classList.add('engine');
      _res.SetFallback();
      // Try to initially contact the server
      sow();
      nextJob();
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
