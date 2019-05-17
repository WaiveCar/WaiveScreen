var dbMap = {},
  // a global pointer to the current job object.
  _last = false,
  _fallback,
  _base = 'http://waivecar-prod.s3.amazonaws.com/',
  _downweight = 0.7,
  _duration = 7.5;

//
// The job schema coming in, copied from the python lib/db.py code:
//
//  'id', 'integer primary key autoincrement'
//  'campaign_id', 'integer'
//  'goal', 'integer'
//  'completion_seconds', 'integer default 0'
//  'last_update', 'datetime default current_timestamp'
//  'job_start',  'datetime'
//  'job_end', 'datetime'
//

function video(what, nobase) {
  var vid = document.createElement('video');
  var src = document.createElement('source');
  vid.setAttribute('preload', 'auto');
  vid.setAttribute('loop', 'true');
  vid.appendChild(src);
  src.src = what;
  return vid; 
}
  
function image(what, nobase) {
  var ext = what.split('.').pop();

  if(['mp4','ogv','mpeg','webm','flv','avi'].includes(ext.toLowerCase()) ) {
    return video(what, nobase);
  }

  var img = document.createElement('img');
  img.onerror = function() {
    if(_fallback.url) {
      this.src = _fallback.url;
      _last.err = 'NOT_FOUND';
    }
  }
  img.onload = function() {
    if(_last && 'err' in _last) {
      delete _last.err;
    }
  }
  if(nobase) {
    img.src = what;
  } else {
    img.src = _base + what;
  }
  img.src_ = what;
  return img;
}

// LRU cache invalidation should eventually exist.
function addJob(job) {
  if(!dbMap[job.campaign_id]) {

    // this acts as the instantiation. 
    // the merging of the rest of the data
    // will come below.
    dbMap[job.campaign_id] = {
      // this is used for comparison to know
      // when we should be flipping the image
      what: job.asset,
      dom: image(job.asset),
      completed_seconds: 0,
    };
  }

  dbMap[job.campaign_id] = Object.assign(
    dbMap[job.campaign_id], job
  );

  return dbMap[job.campaign_id];
}

function post(url, what, cb) {
  var http = new XMLHttpRequest();

  http.open('POST', 'http://localhost:4096/' + url, true);
  http.setRequestHeader('Content-type', 'application/json');

  http.onreadystatechange = function() {
    if(http.readyState == 4 && http.status == 200) {
      cb(JSON.parse(http.responseText));
    }
  }
  
  if(what) {
    http.send(JSON.stringify(what));
  } else {
    http.send();
  }
}

function sow(payload) {
  post('sow', payload, function(res) {
    if(res.res) {
      res.data.forEach(function(row) {
        addJob(row);
      })
    }
  });
}

function prepare(dom) {
  // test if it's a video
  if (dom.pause) {
    dom.currentTime = 0;
    dom.play();
  }
}


function nextad() {
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
    // Here's the range of numbers, calculated by looking at all the remaining things we have to satisfy
    range = Object.values(dbMap).reduce(function (a, b) { return a + b.downweight * (b.goal - b.completed_seconds) }, 0),

    // We do this "dice roll" to see 
    breakpoint = Math.random() * range,
    current, 

    // This is different from our global _duration. In the case of videos we 
    // default to the duration of the video.
    duration,
    prev = _last;

  // If there's nothing we have to show then we fallback to our default asset
  if( range <= 0 ) {
    console.log("Range < 0, using fallback");
    current = _fallback;
  } else {
    let 
      row,
      accum = 0;

    for(key in dbMap) {
      row = dbMap[key];

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

  current.completed_seconds += _duration;

  if(prev) {
    if(prev.what !== current.what) {
      // we reset the downweight -- it can come back
      prev.downweight = 1;

      prev.dom.classList.add('fadeOut');
      current.dom.classList.add('fadeIn');

      prepare(current.dom);
      setTimeout(function() {
        prev.dom.classList.remove('fadeOut');
        document.body.removeChild(prev.dom);
      }, 500);

      document.body.appendChild(current.dom);
    }
    sow({id: current.id, completed_seconds: current.completed_seconds});
  } else {
    current.dom.classList.add('fadeIn');
    prepare(current.dom);
    document.body.appendChild(current.dom);
  }

  current.downweight *= _downweight;

  _last = current;
}

window.onload = function init() {
  /*
  _fallback = {
    what: 'fallback.png',
    dom:  image('fallback.png', true),
    completed_seconds: 0
  };
  sow();
  loop();
  */
  let ix = 0;
  let list = 'out001.mp4 out002.mp4 out003.mp4 out004.mp4 out005.mp4 out006.mp4 out007.mp4 out008.mp4 out009.mp4 out010.mp4 out011.mp4 out012.mp4 out.mp4 output000.mp4 output001.mp4 output002.mp4 output003.mp4 output004.mp4';
  for(let v of list.split(' ')) {

    dbMap[ix++] = {
      // this is used for comparison to know
      // when we should be flipping the image
      what: ix,
      dom: image(v),
      downweight: 1,
      completed_seconds: 0,
      goal: 180,
    };
  }
  nextad();
  //setInterval(nextad, _duration * 1000);
}
