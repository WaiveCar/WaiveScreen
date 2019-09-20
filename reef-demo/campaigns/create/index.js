function calcItems() {
  setTimeout(() => {
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
    document.querySelector('#budget').textContent = `$${budget}`;
    document.querySelector('#cpm').textContent = `$${fakeCPM}`;
    document.querySelector(
      '#impressions',
    ).textContent = `${fakeNumImpressionsPerWeek}`;
  });
}

/*
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

*/
function create_campaign(obj) {
  // Before the payment is processed by paypal, a user's purchase is sent to the server with 
  // the information that has so far been obtained including the picture.
  let formData = new FormData();
  $(document.forms[0]).serializeArray().forEach(function(row) {
    state[row.name] = row.value;
    formData.append(row.name, row.value);
  });
  state.total = dealMap[state.option].price;

  for(var ix = 0; ix < uploadInput.files.length; ix++) {
    formData.append('file' + ix, uploadInput.files[ix]);
  }

  return axios({
    method: 'post',
    url: '/api/campaign',
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
    asset.style.height = '100%';
  } else {
    asset.style.width = '100%';
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
window.onload = function(){
  // The event handler below handles the user uploading new files
  uploadInput = document.getElementById('image-upload');
  uploadInput.addEventListener('change', function() {
    console.log("HI");
    var container = $(".preview-holder");
    container.empty();

    addtime(false);
    Array.prototype.slice.call(uploadInput.files).forEach(function(file) {

      let reader = new FileReader();

      reader.onload = function(e) {
        var asset;

        let row = $(
          ['<div class="screen">',
             '<img src="/assets/screen-black.png" class="bg">',
             '<div class="asset-container"></div>',
          '</div>'].join(''));

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

        $(".asset-container", row).append(asset);
      };
      reader.readAsDataURL(file);
    });
  });
}
