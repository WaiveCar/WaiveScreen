var Engine = function(opts){
  var 
    _res = Object.assign({
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

      doScroll: true,
      doOliver: true,

      target: { width: 1920, height: 675 },

      listeners: {},
      data: {},

      NextJob: false,
    }, opts || {}),
    // This is the actual breakdown of the content on
    // the screen into different partitions
    Strategy = {},
    _id = Engine._length,
    _box = {},
    _start = new Date(),
    _uniq = 0,
    _jobId = 0,
    _downweight = 0.7,
    _nop = () => {},
    _passthru = cb => cb(),
    _log = () => console.log(arguments),
    _stHandleMap = {},
    _key = name => name + '-xA8tAY4YSBmn2RTQqnnXXw',
    _ = {
      debug: false,
      last: false,
      last_sow: [+_start, +_start],
      last_uniq: false,
      last_container: false,
      last_shown: false,
      isNetUp: true,
      current: false,
      firstRun: false,
      fallbackJob: false,
      maxPriority: 0,
    };

  _res._ = _;

  if(_res.dynamicSize) {
    _res.target.width = _res.container.clientWidth;
    _res.target.height = _res.container.clientHeight;
  }

  _res.target.ratio = _res.target.width / _res.target.height;

  function dbg(what) {
    if(!_box.debug) { return; }
    _box.debug.innerHTML += (new Date() - _start) + ": " + what + "\n";
    _box.debug.scrollTo(0,_box.debug.scrollHeight);
  }

  function makeBox(row) {
    if(!_box[row]) {
      _box[row] = document.createElement("div");
      _box[row].className = _key(row);
      return _box[row];
    }
  }

  var _timeout = _res.Timeout = function(fn, timeout, name, override) {
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

  function cleanTimeout(what, dur) {
    return setTimeout(function() { 
      what();
    }, dur);
  }

  function isString(obj) { 
    return !!(obj === '' || (obj && obj.charCodeAt && obj.substr));
  }

  // a little fisher yates to start the day
  function shuffle(array) {
    var currentIndex = array.length;
    var temporaryValue, randomIndex;

    // While there remain elements to shuffle...
    while (0 !== currentIndex) {
      // Pick a remaining element...
      randomIndex = Math.floor(Math.random() * currentIndex);
      currentIndex -= 1;

      // And swap it with the current element.
      temporaryValue = array[currentIndex];
      array[currentIndex] = array[randomIndex];
      array[randomIndex] = temporaryValue;
    }

    return array;
  }

  function event(what, data) {
    if(_.debug) {
      console.log(">>> event[" + _id + "]", what, data);
    }
    _res.data[what] = data;
    if(_res.listeners[what]) {
      _res.listeners[what].forEach(cb => cb(data))
      _res.listeners[what] = _res.listeners[what].filter(cb => !cb.once);
    }
  }
  function on(what, cb) {
    if(_res.data[what]) {
      return cb(_res.data[what]);
    } 
    if(!(what in _res.listeners)) {
      _res.listeners[what] = [];
    }
    _res.listeners[what].push(cb);
    return cb;
  }

  function assetError(obj, e) {
    // TODO we need to report an improperly loading
    // asset to our servers somehow so we can remedy
    // the situation.
    obj.active = false;
    console.log("Making " + obj.url + " inactive");
  }

  function layout() {
    //
    // <div class=topicContainer></div>
    // <div class=top>
    //   <div class=widget></div>
    //   <div class=ad></div>
    // </div>
    // <div class=bottom>
    //   <div class=time></div>
    //   <div class=ticker></div>
    // </div>
    //
    ["topicContainer","top","ad","widget","bottom","time","ticker"].forEach(makeBox);
    // this ordering is correct...trust me.
    _box.top.appendChild(_box.widget);
    _box.top.appendChild(_box.ad);
    _box.bottom.appendChild(_box.time);
    _box.bottom.appendChild(_box.ticker);
    _res.container.appendChild(_box.topicContainer);
    _res.container.appendChild(_box.top);
    _res.container.appendChild(_box.bottom);
    _res.container.classList.add(_key('engine'));
  }

  _res.SetAssetDuration = function(what, index, amount) {
    // Update the total aggregate to reflect the new amount
    what.duration -= (what.duration - amount);

    // Now set the new amount
    what.assetList[index].duration = amount;
  }

  function image(asset, obj) {
    var img = document.createElement('img');
    img.onerror = function(e) {
      assetError(asset, e);
    }
    img.onload = function(e) {
      if(e.target.width) {
        var container = _res.container.getBoundingClientRect();
        var parentratio = container.width/container.height;
        var ratio = e.target.width / e.target.height;
        if(parentratio > ratio) {
          e.target.style.width = '100%';
        } else {
          e.target.style.height = '100%';
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
    asset.run = function(cb) {
      var container = _res.container.getBoundingClientRect();
      var parentratio = container.width/container.height;
      var ratio = img.width / img.height;
      if(parentratio > ratio) {
        img.style.width = '100%';
        img.style.height = 'auto';
      } else {
        img.style.width = 'auto';
        img.style.height = '100%';
      }
      return cb && cb();
    }
    asset.pause = asset.rewind = asset.play = _nop;
    asset.dom = img;
    asset.type = 'image';
    return asset;
  }

  function iframe(asset, obj) {
    var dom = document.createElement('iframe');
    dom.src = asset.url;
    asset.dom = dom;
    asset.rewind = asset.pause = asset.play = _nop;
    asset.run = _passthru;
    asset.active = true;
    asset.duration = asset.duration || 1000 * _res.duration;
    obj.duration += asset.duration;
    obj.active = true;
    asset.type = 'iframe';
    return asset;
  }
  
  function video(asset, obj) {
    var vid = document.createElement('video');
    var src = document.createElement('source');
    var mylock = false;
    var mycb;

    vid.setAttribute('muted', true);
    //vid.setAttribute('preload', 'auto');
    vid.appendChild(src);

    src.src = asset.url;
    asset.dom = vid;

    asset.cycles = 1;
    asset.pause = vid.pause;
    asset.play = vid.play;
    asset.rewind = function() {
      vid.currentTime = 0;
    }
    asset.run = function(cb) {
      mycb = cb;
      vid.currentTime = 0;
      vid.volume = 0;
      var now = new Date();
      var playPromise = vid.play();

      if (playPromise !== undefined) {
        playPromise.then(_nop)
        .catch(function(e) {
          console.log('unplayable', _id, asset.uniq, e.message, e.name, asset, vid.duration, vid.currentTime);
          if(new Date() - now < 100) {
            // if we were interrupted in some normal interval, maybe it will just work
            // if we try again ... might as well - don't reset the clock though.
            //asset.run(true);
          }
          //asset.active = false;
        });
      }
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
        // console.log(asset.url + " is " + asset.duration + "s. Looping " + asset.cycles + " times");
        asset.duration *= asset.cycles;
      }
      vid.muted = true;
      if(vid.videoWidth) {
        var container = _res.container.getBoundingClientRect();
        var parentratio = container.width/container.height;
        var ratio = vid.videoWidth / vid.videoHeight;
        if(ratio > parentratio) {
          vid.style.width = '100%';
        } else {
          vid.style.height = '100%';
        }
        /*
          var maxHeight = _res.target.width * vid.videoHeight / vid.videoWidth;
          vid.style.height =  Math.min(_res.target.height, maxHeight * 1.2) + "px";
          vid.style.width = _res.target.width + "px";
        } else { 
          var maxWidth = _res.target.height * vid.videoWidth / vid.videoHeight;
          vid.style.width =  Math.min(_res.target.width, maxWidth * 1.2) + "px";
          vid.style.height = _res.target.height + "px";
        }
        */
      } 
      obj.duration += asset.duration;
      obj.active = true;
    }

    // notice this is on the src assetect and not the vid
    // containers.
    src.onerror = function(e) {
      assetError(asset, e);
    }

    vid.addEventListener('play', function() {
      if(mycb) {
        mycb();
      }
      mylock = false;
    });

    /* 
    var m = ["emptied","ended","loadeddata","play","playing","progress","seeked","seeking","pause"];
    for(var ix = 0; ix < m.length; ix++) {
      (function(row) {
        vid.addEventListener(row, function() {
          self.vid = vid;
          console.log(+new Date(), _id, asset.uniq, row, vid.duration, vid.currentTime);
        });
      })(m[ix]);
    }
    */

    asset.type = 'video';
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

  // Similar to makeJob, we intend to come out of this
  // with {url: <str>, duration: <int>, ... } AND the
  // actual DOM object that will sit on the screen.
  function urlToAsset(row, obj) {
    var asset = isString(row) ? {url: url} : row;
    if(!asset.container){ 
      var container = document.createElement('div');
      container.classList.add(_key('container'));

      if(assetTest(asset, 'image', ['png','jpg','jpeg'])) {
        asset = image(asset, obj);
      } else if(assetTest(asset, 'video', ['mp4', 'avi', 'mov', 'ogv'])) {
        asset = video(asset, obj);
        container.classList.add("hasvideo");
      } else {
        asset = iframe(asset, obj);
      }
      asset.uniq = _uniq++;
      asset.container = container;
      asset.container.appendChild(asset.dom);
    }
    return asset;
  }

  // All the things returned from this have 2 properties
  // 
  //  run() - for videos it resets the time and starts the video
  //  duration - how long the asset should be displayed.
  //
  // Essentially the obj has the properties:
  //
  //  {
  //    asset_meta:  [
  //      { 
  //        url:
  //        duration:
  //      } ...
  //    ]
  //  }
  //
  // If we pass something in with asset_meta, that's fine.
  // If we pass in a string, then it's the url of one asset
  // If we pass in {url: blah} then it becomes 1 asset.
  //
  function makeJob(obj) {
    if( isString(obj) ) {
      obj = {asset_meta: [{ url: obj }] };
    } else if('url' in obj) {
      obj.asset_meta = [{ url: obj.url }];
    }

    // We want the object to actually take
    // these values as references while also
    // accepting overrides. so we are doing 
    // it twice.
    //
    // Now you may think that assign(a,{},a) will work
    // BUT THERE YOU WOULD BE WRONG. It's probably a
    // bug in chromium ... anyway.
    //
    Object.assign(obj, 
      Object.assign({
        downweight: 1,
        completed_seconds: 0,
        // We need multi-asset support on a per-job
        // basis which means we need to be able
        // to track
        position: 0,
        // This is the total duration of all the
        // assets included in this job.
        duration: 0,
        asset_original: JSON.parse(JSON.stringify(obj.asset_meta)),
        assetList: [],
        id: _jobId++,
      }, obj)
    );
    
    obj.assetList = obj.asset_meta.map(row => urlToAsset(row, obj));

    obj.remove = function(what) {
      obj.assetList = obj.assetList.filter(row => row.uniq != what.uniq );
      obj.duration = obj.assetList.reduce((a,b) => { a + b.duration }, 0);
    }

    obj.append = function(what) {
      var asset = urlToAsset(what, obj);
      obj.assetList.push(asset);
      return asset;
    }
        
    return obj;
  }

  // LRU cache invalidation should eventually exist.
  function addJob(job) {
    if(!_res.db[job.campaign_id]) {

      // This acts as the instantiation. 
      // the merging of the rest of the data
      // will come below.
      _res.db[job.campaign_id] = makeJob(job);
    }

    // This places in things like the goal
    _res.db[job.campaign_id] = Object.assign(
      _res.db[job.campaign_id], job
    );

    return _res.db[job.campaign_id];
  }

  // TODO: A circular buffer to try and navigate poor network
  // conditions.
  function remote(verb, url, what, onsuccess, onfail = _log) {
    if(!_res.server) {
      return onfail();
    }
    remote.ix++;

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
        if(http.status == 200) {
          _.isNetUp = true;
          var res = JSON.parse(http.responseText);

          if(res.res === false) {
            onfail(res.data, http.responseText);
          } else {
            onsuccess(res, http.responseText);
          }
        } else if(http.status == 500 && onfail) {
          onfail();
        }
      }
    }

    http.onabort = http.onerror = http.ontimeout = function() {
      if(onfail) {
        onfail();
      }
      // ehhh ... maybe we just can't contact things?
      _.isNetUp = false;
      remote.lock[url] = false;
    }
    
    if(what) {
      return http.send(JSON.stringify(what));
    } 
    http.send();
  }
  remote.lock = {};
  remote.ix = 0;

  function get(url, onsuccess, onfail) {
    return remote('GET', url, false, onsuccess, onfail);
  }
  function post(url, what, onsuccess, onfail) {
    return remote('POST', url, what, onsuccess, onfail);
  }

  function forgetAndReplace(list) {
    _res.db = {};
    list.forEach(row => addJob(row));
  }
  function sow(payload, cb) {
    // No server is set
    if(!_res.server) {
      remote.ix++;
      return;
    }

    post('sow', payload, function(res) {
      // This has to be somehow optional because
      // it's not always applicable
      if(res.res) {
        sow.strategy(res.data);
      }
      return cb && cb();
    });
  }

  var scrollIval;
  function scrollIfNeeded(){
    if(!_res.doScroll) { 
      return;
    }
    var p = _.current.shown.dom;
    function scroll(obj, dim) {
      var 
        anchor  = dim == 'vertical' ? 'marginTop' : 'marginLeft',
        dom  = obj.dom,
        goal = obj.goal,
        time = obj.duration || _res.duration * 1000;
        period = 1000 / 40,
        rounds = time / period,
        step = goal / rounds,
        ix = 0;

      clearInterval(scrollIval);

      scrollIval = setInterval(function() {
        if (ix++ >= rounds) {
          clearInterval(scrollIval);
        }
        dom.style[ anchor ] = -(Math.min(ix * step, goal)) + "px";
      }, period);
    }
    p.style.marginTop = p.style.marginLeft = 0;
    setTimeout(function(){
      var
        opts = {dom: p, duration: 0.7 * _.current.shown.duration * 1000},
        el = p.getBoundingClientRect(),
        box = p.parentNode.getBoundingClientRect();

      if(box.height < p.height * .8) {
        opts.goal = p.height - box.height;
        scroll(opts, 'vertical');
      } else if (box.width < p.width * .8) {
        opts.goal = p.width - box.width;
        scroll(opts, 'horizontal');
      }
    }, _.current.shown.duration * .15 * 1000);
  }

  // Jobs have assets. NextJob chooses a job to run and then asks nextAsset
  // to do that work ... when nextAsset has no more assets for a particular job
  // it calls NextJob again.
  function nextAsset() {
    var prev, timeoutDuration = 0, didRun = false, doFade = false;

    //console.log(new Error().stack);
    if(_res.pause) {
      return;
    }
    // If we are at the start of our job
    // then this is the only valid time we'd
    // be transitioning away from a previous job
    //
    // so this is when we do the reporting.
    if(_.current.position === 0 && _.last) {

      // If this exists then it'd be set at the last asset
      // previous job.
      // We can state that we've shown all the assets that
      // we plan to show
      _.last.completed_seconds += _.last.duration;

      // and report it up to the server
      sow({
        start_time: _.last_sow[0],
        end_time: _.last_sow[1],
        job_id: _.last.job_id,
        campaign_id: _.last.campaign_id, 
        completed_seconds: _.last.completed_seconds
      });

      if(_.last.job_id !== _.current.job_id) {
        // we reset the downweight -- it can come back
        _.last.downweight = 1;
      }
    }

    // If we are at the end then our next function should be to
    // choose the next job.
    if(_.current.assetList && _.current.position === _.current.assetList.length) {
      event('jobEnded', _.current);
      return _res.NextJob();
    } 

    _.current.shown = _.current.assetList[_.current.position];
    _.current.shown.run( function() {
      if(_.current.shown.container.parentNode !== _box.ad || _.current.shown.forceReload) {
        _box.ad.appendChild(_.current.shown.container);
      }
      if(_.current.shown.type == 'image') {
        scrollIfNeeded();
      }
      didRun = true;
    });

    if(_.last_container && _.current.shown.uniq != _.last_uniq) {
      // This is NEEDED because by the time 
      // we come back around, _.last.shown will be 
      // redefined.
      prev = _.last_container;
      prev.classList.add(_key('fadeOut'));
      _timeout(function() {
        // the second part is there because this bug is still
        // somehow around. We really need to squash it.
        if(didRun && prev.parentNode === _box.ad) {
          prev.classList.remove(_key('fadeOut'));
          _box.ad.removeChild(prev);
        }
      }, _res.fadeMs, 'assetFade');
      doFade = true;
    }

    _.last_uniq = _.current.shown.uniq;
    _.last_container = _.current.shown.container;
    _.last_shown = _.current.shown;

    _.current.shown.container.classList[doFade ? 'add' : 'remove' ](_key('fadeIn'));

    // These will EQUAL each other EXCEPT when the position is 0.
    _.last = _.current;

    // And we increment the position to show the next asset
    // when we come back around
    _.current.position ++;

    timeoutDuration = Math.max(_.current.shown.duration * 1000 - _res.fadeMs / 2, 1000);

    _timeout(nextAsset, timeoutDuration, 'nextAsset');
  }

  function setNextJob(job) {
    _.current = job;
    if(_.current) {
      _.current.downweight *= _downweight;
      _.current.position = 0;
    }
    // which is consistent between the two time stores.
    _.last_sow[0] = _.last_sow[1];
    _.last_sow[1] = +new Date();
    return job;
  }

  Strategy.set = function(what) {
    Strategy.current = what;
    Strategy[what].enable();
    // Make sure we don't try anything until we get a default
    on('system', _res.NextJob).once = true;
  };

  Strategy.Oliver = (function( ) {
    var topicMap = {},
      // we can override this when we get the
      // default.
      topicList = [],
      current = false,
      jobIx = 0,
      activeList = [],
      doReplace = true,
      topicIx = 0;

    function render(forceOff) {
      if(forceOff || !topicList[topicIx].internal) {
        _res.container.classList.remove('hasTopicList');
      } else {
        _res.container.classList.add('hasTopicList');
        // make only the active topicList
        _box.topicList.forEach((row, ix) => row.classList[ix === topicIx ? 'add' : 'remove'](_key('active')));
      }
    }

    function nextTopic() {
      //
      // Essentially we gather all the active jobs, then we group
      // them by "topic" which is a field in the campaign.
      // Amongst each topic we arrange them by order of how
      // much of our "contract" we need to play out and then
      // just go through that list.
      //
      // The only real catch here is we don't change our idea
      // of what jobs are applicable to us until the current
      // topic is exhausted. 
      //
      // Even then because we want to commit to at least some 
      // form of continuity, if the new set does not contain 
      // jobs of the next topic then we go to it anyway and 
      // show some default campaign associated with that topic.
      //
      // This method *ONLY* looks not broken if we commit
      // ourselves to having a limited number of topics we
      // can choose from.  
      //

      activeList = Object.values(_res.db).filter(row => row.duration);

      //
      // We need to clear out our local copy of the ads
      // and repopulate.
      //
      topicMap = {};

      activeList.forEach(row => {
        // The null case is actually ok here.
        if (!topicMap[row.topic]) {
          topicMap[row.topic] = [];
        }
        //
        // This may be fairly inefficient since we are remaking
        // jobs that we may have previously made.
        //
        topicMap[row.topic].push(makeJob(row));
      });

      topicIx = (topicIx + 1) % topicList.length;
      jobIx = 0;

      // So we know our topic now, it's topicIx, which is an
      // integer offset in topicList
      //
      // This could be null or empty, fine ... but
      // it's kinda the server's responsibility to
      // make sure there's default campaigns for each
      // of these.
      current = topicMap[topicList[topicIx].internal];

      if(!current) {
        current = topicMap[null];
      }

      //console.log(_id, current, activeList, topicMap, _res.db);

      render();
      nextJob();
    }

    function nextJob() {
      if(!current) {
        // This means we've really fucked up somehow
        doReplace = true;
        if(!_.fallbackJob) {
          console.warn(_id, "I'm at a nextJob but have no assets or fallbacks");
          return _timeout(_res.NextJob, 1500, 'nextJob');
        }
        setNextJob(_.fallbackJob);

        // Force the topics off for now.
        render(true);

        // nextAsset is at the bottom
      } else {
        // console.log(topicMap, current, jobIx, topicList);
        
        if(jobIx === current.length) {
          nextTopic();
        }
        //
        // We are assuming a bunch here. essentially that we
        // have hit the nextTopic to assign a current pointer 
        // and that our sequential revisiting will handle our
        // mechanics correctly.
        //
        setNextJob( current[jobIx] );
        jobIx++;

        //
        // We'll go to the next topic at the end of showing
        // our ad. However, we need to make sure that we have
        // flagged our sow strategy to replace before we 
        // go into our timeout.
        // 
        if(jobIx === current.length) {
          doReplace = true;
        }
      }
      nextAsset();
    }

    function forgetAndReplaceWhenFlagged(list) {
      if(doReplace) {
        doReplace = false;
        forgetAndReplace(list);
      }
    }

    function newTopic() {
      var dom = document.createElement('div');
      dom.className = _key('topic');
      _box.topicContainer.appendChild(dom);
      return dom;
    }

    function enable() {
      // This enables the top category and swaps out the nextJob with us
      _res.NextJob = nextTopic;
      _box.topicList = [];
      setTopicList([
        {internal: 'event', display: 'Events'},
        {internal: 'help', display: 'Notices'},
        {internal: 'service', display: 'Services'}
      ]);
      sow.strategy = forgetAndReplaceWhenFlagged;
    }

    function setTopicList(list) {
      for(var ix = _box.topicList.length; ix < list.length; ix++) {
        _box.topicList.push(newTopic());
      }
      topicList = list;
      topicList.forEach((row, ix) => _box.topicList[ix].innerHTML = row.display);
      topicList.push( {internal: null, display: null} );
      render();
    }

    return { setTopicList, nextJob, enable };
  })();

  Strategy.Freeform = (function() {
    return {
      enable: function() {
        _res.nextJob = Freeform.nextJob;
        sow.strategy = forgetAndReplace;
      },
      nextJob: function () {
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
          row, accum = 0,
          activeList = Object.values(_res.db).filter(row => row.active && row.duration),// && row.filter === maxPriority),

          // Here's the range of numbers, calculated by looking at all the remaining things we have to satisfy
          range = activeList.reduce( (a,b) => a + b.downweight * (b.goal - b.completed_seconds), 0),

          // We do this "dice roll" to see 
          breakpoint = Math.random() * range;

        if(_.debug) {
          console.log({active: activeList, db:_res.db, range: range, priority: _.maxPriority});
        }
        // If there's nothing we have to show then we fallback to our default asset
        if( range <= 0 ) {

          if(!_.fallbackJob) {
            // woops what do we do now?! 
            // I guess we just try this again?!
            return _timeout(_res.NextJob, 1500, 'nextJob');
          }

          setNextJob(_.fallbackJob);

          if(!_.firstRun && activeList.length == 0 && Object.values(_res.db) > 1) {
            // If we just haven't loaded the assets then
            // we can cut the duration down
            _res.SetAssetDuration(_.current, 0, 0.2);
          } else {
            // Otherwise we have satisfied everything and
            // maybe just can't contact the server ... push
            // this out to some significant number
            _res.SetAssetDuration(_.current, 0, _res.duration);
          }

        } else {
          // This is needed for the end case.
          _.firstRun = true;
          _.current = false;
          for(row of activeList) {

            accum += row.downweight * (row.goal - row.completed_seconds);
            if(accum > breakpoint) {
              setNextJob(row);
              break;
            }
          }
          if(!_.current) {
            setNextJob(row);
          }
        }

        nextAsset();
      }
    };
  });

  function SetFallback (assetList, force) {
    _res.fallback = _res.fallback || assetList;

    // We look for a system default
    if(_res.server && (force || !_res.fallback)) {
      // If we have a server we can get it from there
      return get('/default', function(res) {
        _.fallbackJob = makeJob(res.data.campaign);

        if(_res.data.topicList) {
          Strategy.Oliver.setTopicList(_res.data.topicList);
        }
        _res.system = res.data.system;
        event('system', _res.system);

        // This is our strategy to look for 
        // updated default campaigns every 
        // few minutes (#130)
        _timeout(() => SetFallback(false, true), 3 * 60 * 1000, 'setFallback');

      }, function() { 
        _timeout(
          cleanTimeout(SetFallback, _res.duration * 1000), 
          _res.duration * 1000, 'setFallback', true);
      });

    } 
    if(_res.fallback) {
      _.fallbackJob = makeJob(_res.fallback);
    }
    event('system', {});
  }

  // A repository of engines
  Engine[Engine._length++] = _res;

  // This makes sure the _box references are valid before
  // running Start().
  layout();

  // Our strategy of displaying ads
  Strategy.set(_res.doOliver ? 'Oliver' : 'Freeform');

  // The convention we'll be using is that
  // variables start with lower case letters,
  // function start with upper case.
  return Object.assign(_res, {
    Strategy, SetFallback, on, _,

    Play: function() {
      _res.pause = false;
      if(_.current) {
        _.current.shown.play();
        return nextAsset();
      } 
      _res.NextJob();
    },
    Pause: function() {
      _res.pause = !_res.pause;
      clearTimeout(_stHandleMap.nextAsset.handle);
      _.current.shown.pause();
    },

    PlayNow: function(job, doNotModify) {
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
      var div = makeBox('debug');
      _.debug = true;

      if(div) {
        _box.top.appendChild(div);
      }

      return Object.assign({ _box }, _);
    }, 
    Start: function(){
      // Try to initially contact the server
      sow();
      _res.SetFallback();
      // This is a race condition, the on(system) should fire this off.
      //_res.NextJob();
    },
    AddJob: function(obj, params) {
      if(isString(obj)) {
        obj = {url: obj};
      }

      var job = makeJob(obj || {});
      // this allows someone to set say,
      // the priority to a high number
      _res.db[job.id] = Object.assign(job, params);
      return _res.db[job.id];
    }
  });
};

Engine._length = 0;
