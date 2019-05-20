var Engine = function(opts){
  var 
    _res = Object.assign({
      // This is what the ads attach to
      container: document.body,

      // If a server is set, then the progress gets posted
      // off to it - also new assets and jobs can come from it.
      server: false,

      fallback: 'fallback.png',

      db: {},

      base: 'http://waivecar-prod.s3.amazonaws.com/',
    }, opts || {}),
    _last = false,
    _downweight = 0.7,
    _nop = function(){},
    _isNetUp = true,
    _fallback,
    _duration = 7.5;


  function assetError(obj, e) {
    // TODO we need to report an improperly loading
    // asset to our servers somehow so we can remedy
    // the situation.
    obj.active = false;
    console.log("Making " + obj.url + " inactive");
  }

  function video(obj) {
    var vid = document.createElement('video');
    var src = document.createElement('source');

    vid.setAttribute('preload', 'auto');
    vid.setAttribute('loop', 'true');
    vid.appendChild(src);

    src.src = obj.url;
    obj.dom = vid;

    obj.run = function() {
      vid.currentTime = 0;
      vid.play();
    }

    vid.ondurationchange = function(e) {
      // This will only come if things are playable.
      obj.duration = obj.duration || e.target.duration;
      obj.active = true;
    }

    // notice this is on the src object and not the vid
    // containers.
    src.onerror = function(e) {
      assetError(obj, e);
    }

    return obj;
  }
    
  // All the things returned from this have 2 properties
  // 
  //  run() - for videos it resets the time and starts the video
  //  duration - how long the asset should be displayed.
  //
  function makeAsset(obj) {
    obj.downweight = obj.downweight || 1;
    obj.completed_seconds = obj.completed_seconds || 0;
    obj.what = obj.what || obj.url;

    //
    // We don't want to manually set this.
    // obj.goal
    //

    var ext = obj.url.split('.').pop();
    if(['mp4','ogv','mpeg','webm','flv','3gp','avi'].includes(ext.toLowerCase()) ) {
      obj = video(obj);
    } else {

      var img = document.createElement('img');

      obj.active = true;
      obj.duration = obj.duration || _duration;
      console.log("Yeah I'm here", _nop, _duration, _last);
      obj.run = _nop;
      obj.dom = img;

      img.onerror = function(e) {
        assetError(obj, e);
      }
      img.onload = function() {
        obj.active = true;
      }
      img.src = obj.url;
    }
      
    return obj;
  }

  // LRU cache invalidation should eventually exist.
  function addJob(job) {
    if(!_res.db[job.campaign_id]) {

      // this acts as the instantiation. 
      // the merging of the rest of the data
      // will come below.
      _res.db[job.campaign_id] = makeAsset({ url: job.asset });
    }

    _res.db[job.campaign_id] = Object.assign(
      _res.db[job.campaign_id], job
    );

    return _res.db[job.campaign_id];
  }

  // TODO: A circular buffer to try and navigate poor network
  // conditions.
  function post(url, what, cb) {
    post.ix = (post.ix + 1) % post.size;

    if(post.lock) {
      console.log("Not posting, locked on " + post.lock);
      return false;
    }
    // Try to avoid a barrage of requests
    post.lock = post.ix;

    var http = new XMLHttpRequest();

    http.open('POST', _res.server + url, true);
    http.setRequestHeader('Content-type', 'application/json');

    http.onreadystatechange = function() {
      if(http.readyState == 4) {
        post.lock = false;
        if( http.status == 200) {
          _isNetUp = true;
          cb(JSON.parse(http.responseText));
        }
      }
    }

    http.onabort = http.onerror = http.ontimeout = http.onloadend = function(){
      // ehhh ... maybe we just can't contact things?
      _isNetUp = false;
      post.lock = false;
    }
    
    if(what) {
      http.send(JSON.stringify(what));
    } else {
      http.send();
    }
  }
  post.size = 5000;
  post.ix = 0;

  function sow(payload) {
    // no server is set
    if(!_res.server) {
      if(post.ix == 0) {
        console.info("No server is set.");
      }
      post.ix++;
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

  function nextAd() {
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

      // We do this "dice roll" to see 
      breakpoint = Math.random() * range,
      current;

    // If there's nothing we have to show then we fallback to our default asset
    if( range <= 0 ) {
      console.log("Range < 0, using fallback");
      current = _fallback;
      if(activeList.length == 0) {
        // If we just haven't loaded the assets then
        // we can cut the duration down
        current.duration = 0.1;
      } else {
        // Otherwise we have satisfied everything and
        // maybe just can't contact the server ... push
        // this out to some significant number
        current.duration = 20;
      }

    } else {
      let accum = 0;

      for(let row of activeList) {

        accum += row.downweight * (row.goal - row.completed_seconds);
        if(accum > breakpoint) {
          current = row;
          break;
        }
      }
      if(!current) {
        current = row;
      }
    }
    console.log(current);

    // 
    // By this time we know what we plan on showing.
    //
    current.completed_seconds += current.duration;
    current.downweight *= _downweight;

    if(!_last || _last.what != current.what) {
      if(_last) {
        // we reset the downweight -- it can come back
        _last.downweight = 1;
        _last.dom.classList.add('fadeOut');

        // This is NEEDED because by the time 
        // we come back around, _last will be 
        // redefined.
        let prev = _last;
        setTimeout(function() {
          prev.dom.classList.remove('fadeOut');
          _res.container.removeChild(prev.dom);
        }, 500);
      }

      current.dom.classList.add('fadeIn');
      current.run();
      _res.container.appendChild(current.dom);

      // This is a problem because we are stating they are completed prior
      // to them actually running - this is more about what we "plan" to do
      sow({id: current.id, completed_seconds: current.completed_seconds});
    }

    _last = current;
    setTimeout(nextAd, current.duration * 1000);
  }

  _res.start = function(){
    _res.container.classList.add('engine');
    _res.setFallback();
    nextAd();
  }
  _res.setFallback = function(url) {
    _res.fallback = _res.fallback || url;
    _fallback = makeAsset({url: _res.fallback, duration: .1});
  }
  _res.addAsset = function(obj) {
    obj = makeAsset(obj);
    var id = obj.id || obj.what;
    _res.db[id] = obj;

    var res = {};
    res[id] = obj;
    return res;
  }

  return _res;
};
