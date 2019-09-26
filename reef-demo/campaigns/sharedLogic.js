var 
  _preview,
  _assetList = [];

function calcItems() {
  requestAnimationFrame(() => {
    let schedule = JSON.parse($('#schedule').jqs('export'));
    let minutesPerWeek = schedule.reduce((acc, item) => {
      return (
        acc +
        item.periods.reduce((acc, period) => {
          return (
            acc +
            moment(period.end, 'hh:mm').diff(
              moment(period.start, 'hh:mm'),
              'minutes',
            )
          );
        }, 0)
      );
    }, 0);
    let budget = document.querySelector('#budget').value;
    let fakeNumImpressionsPerWeek = budget * 14.32;
    let fakeCPM = (fakeNumImpressionsPerWeek / budget / 100).toFixed(2);
    if (budget) {
      document.querySelector('#budget').textContent = `$${budget}`;
      document.querySelector('#cpm').textContent = `$${fakeCPM}`;
      document.querySelector(
        '#impressions',
      ).textContent = `${fakeNumImpressionsPerWeek}`;
    }
  });
}

(() => {
  $('#schedule').jqs();
  document
    .getElementById('campaign-budget')
    .addEventListener('change', calcItems);
  document
    .getElementById('campaign-budget')
    .addEventListener('keyup', calcItems);
  document
    .querySelector('.jqs-table tbody')
    .addEventListener('mouseup', calcItems);
})();

function create_campaign(obj) {
  // Before the payment is processed by paypal, a user's purchase is sent to the server with 
  // the information that has so far been obtained including the picture.
  let formData = new FormData();
  $(document.forms[0]).serializeArray().forEach(function(row) {
    state[row.name] = row.value;
    formData.append(row.name, row.value);
  });
  state.total = dealMap[state.option].price;

  /*
  for(var ix = 0; ix < uploadInput.files.length; ix++) {
    formData.append('file' + ix, uploadInput.files[ix]);
  }
  */
  for(var ix = 0; ix < _job.assetList.length; ix++) {
    formData.append('file' + ix, _job.assetList[ix]);
  }

  return axios({
    method: 'post',
    url: 'http://192.168.86.58/api/campaign',
    data: formData,
    config: {
      headers: { 'Content-Type': 'multipart/form-data' },
    },
  }).then(function(resp) {
    if(resp.res) {
      state.campaign_id = res.data;
    }
    if(!obj) {
      return true;
    }
    return obj.payment.create({
      payment: {
        transactions: [
          {
            amount: {
              total: (state.total / 100).toFixed(2),
              currency: 'USD',
            }
          }
        ]
      }
    });
  });
}
function resize(asset, width, height) {
  if( height * (1920/756) > width) {
    asset.style.width = '100%';
  } else {
    asset.style.height = '100%';
  }
}
function addtime(n) {
  if(n === false) {
    duration = 0;
    $("#runtime").hide();
  } else {
    duration += n;
    if(duration == 0) {
      $("#runtime").hide();
    } else {
      $("#runtime").html("Runtime: " + duration.toFixed(2) + " sec").show();
    }
  }
}
function setRatio(container, what) {
  if(what == 'car') {
    container.style.height = (.351 * container.clientWidth) + "px";
  }
}

function get(ep, cb) {
  fetch(new Request(`/api/${ep}`))
    .then(res => {
      if (res.status === 200) {
        return res.json();
      }
    }).then(cb);
}

function post(ep, body, cb) {
  fetch(new Request(`http://192.168.86.58/api/${ep}`, {
    method: 'POST', 
    body: JSON.stringify(body)
  })).then(res => {
    if (res.status === 200) {
      return res.json();
    }
  }).then(cb);
}

var _shown = false;
function show(what) {
  if(_shown && _shown != what) {
    $(`.${_shown}-wrapper`).slideUp();
  }
  $(`.${what}-wrapper`).slideDown(function() {
    if(what == 'creatives') {
      setRatio(_container, 'car'); 
    }
  });
  _shown = what;
}

function doMap() {
  $.getJSON("http://192.168.86.58/api/screens?active=1&removed=0", function(Screens) {
    self._map = map({points:Screens});
    let success = false;

    if(success) {
      _map.load(_campaign.shape_list);
    } else {
      _map.center([-118.34,34.06], 11);
    }
  });
}

function clearmap() {
  _map.clear();
}

function removeShape() {
  _map.removeShape();
}

function geosave() {
  var coords = _map.save();
  // If we click on the map again we should show the updated coords
  _campaign.shape_list = coords;
  post('campaign_update', {id: _id, geofence: coords}, res => {
    show({data: 'Updated Campaign'}, 1000);
  });
}

function instaGet() {
  var user;
  function Gen() {
    $(".insta .selector").remove();
    var ix = 1;
    var selected = [];
    selector.forEach(function(row) {
      row.innerHTML += `<div class=selector>${ix}</div>`;
      ix++;
      selected.push(row.dataset.standard);
    })
    var param = selected.map(row => `images[]=${row}`).join('&');
    $('.insta .preview').attr('src', `/insta.php?user=${user.username}&${param}`);
  }
  var selector = [];
  self.s = selector;
  get('instagram?info=1', function(res) {
    $(".insta .loader").slideUp();
    if(!res.res) {
      $(".insta .login").css("display","flex");
      return;
    }
    res = res.data;
    user = res.data[0].user;
    var row, content = [];
    $('.insta .profile img').attr('src', user.profile_picture);
    $('.insta .info .name').html( user.username );
    $('.insta .info .description').html( user.full_name );
    for(var ix = 0; ix < res.data.length; ix++) {
      if(!(ix % 3)) {
        if(row) {
          content.push("<div class=row>" + row.join('') + "</div>");
        }
        row = [];
      }
      var big = res.data[ix].images.standard_resolution.url,
          small = res.data[ix].images.thumbnail.url;
      row.push( `<div class='box' data-standard='${big}'><img src=${small}></div>`);
    }
    if(row) {
      content.push("<div class=row>" + row.join('') + "</div>");
    }
    $('.insta .content').html( content.join('') );
    setTimeout(function(){
      $(".insta .content .box").each(function() {
        console.log(this);
        if(selector.length < 6) {
          selector.push(this);
        }
      });
      Gen();
    }, 10);
    $(".insta .content .box").click(function() {
      var exists = selector.filter(row => row.dataset.standard == this.dataset.standard);
      if(exists.length) {
        selector = selector.filter(row => row.dataset.standard != this.dataset.standard);
      } else {
        if(selector.length < 6) {
          selector.push(this);
        } else {
          // don't gen.
          return;
        }
      }
      Gen();
    });
    $(".insta .mock").fadeIn(1000);

  });
}



window.onload = function(){
  self._container =  document.getElementById('engine');
  doMap();
  var isFirst = true;
  if (self._container) {
    setRatio(_container, 'car'); 
    self._preview = Engine({ 
    container: _container,
    dynamicSize: true,
    _debug: true });
  self._job = _preview.AddJob();

  instaGet();
  $(".controls .rewind").click(function() {
    // this is a lovely trick to force the current job
    // which effectively resets itself
      _preview.PlayNow(_job, true);
    });
  }

  $(".ratios button").click(function(){
    $(this).siblings().removeClass('active');
    $(this).addClass('active');
    if(this.innerHTML == "16:9") {
      _container.style.width = _container.clientHeight * 16/9 + "px";
    } else if(this.innerHTML == "3:2") {
      _container.style.width = _container.clientHeight * 3/2 + "px";
    } else {
      _container.style.width = "100%";
    }
  });


  // The event handler below handles the user uploading new files
  uploadInput = document.getElementById('image-upload');
    if (uploadInput) {
    uploadInput.addEventListener('change', function() {
      var container = $(".preview-holder");

      addtime(false);
      Array.prototype.slice.call(uploadInput.files).forEach(function(file) {

        let reader = new FileReader();

        reader.onload = function(e) {
          var asset, reference;

          let row = $(
            ['<div class="screen">',
               '<img src="/screen-black.png" class="bg">',
               '<button type="button" class="remove-asset btn btn-sm btn-dark">',
               '<i class="fas fa-times"></i>',
               '</button>',
               '<div class="asset-container"></div>',
            '</div>'].join(''));

          reference = _job.append(e.target.result);

          if(file.type.split('/')[0] === 'image') {
            asset = document.createElement('img');
            asset.onload = function() {
              resize(asset, asset.width, asset.height);
              container.append(row);
              addtime( 7.5 );
            }

            asset.src = e.target.result;
            asset.className = 'asset';
          } else {
            asset = document.createElement('video');
            var src = document.createElement('source');

            asset.setAttribute('preload', 'auto');
            asset.setAttribute('loop', 'true');
            asset.appendChild(src);

            src.src = e.target.result;

            asset.ondurationchange = function(e) {
              asset.currentTime = 0;
              asset.play();
              resize(asset, asset.videoWidth, asset.videoHeight);
              container.append(row);
              addtime( e.target.duration );
            }
          }

          $(".remove-asset", row).click(function() {
            _job.remove(reference);
            row.remove();
          });

          $(".asset-container", row).append(asset);
        };
        reader.readAsDataURL(file);
      });

      if(isFirst) {
        _preview.Play();
        isFirst = false;
      }
    });
  }
}

