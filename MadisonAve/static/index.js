var dealMap = {
    testdrive: { price: 100 },
    shoestring: { price: 999 },
    standard: { price: 2999 }
  }, 
  duration = 0,
  fileList = [],
  uploadInput,
  // This 'state' is used to store anything that is needed within this scope
  state = { 
    allLocations: [{
      id: 1,
      label: "Santa Monica",
      name: "santamonica",
      image: "sm-day.jpg",
    }, {
      id: 2,
      label: "Anywhere in LA",
      name: "la",
      image: "traffic-morning.jpg",
    }, {
      id: 3,
      label: "Hollywood",
      name: "hollywood",
      image: "hollywood-night.jpg",
    }]
  };

function selectLocation(what) {
  $(what).siblings().removeClass('checked');
  $(what).addClass('checked');
  $("input", what).prop('checked', true);
}

function fakebuy() {
  alert("Thanks!! That's it!!");
  create_campaign();
  fakebuy = function() {
    alert("No I'm serious, go away");
  }
}

function price(amount) {
  return '$' + (parseInt(amount, 10)/100).toFixed(2);
}

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

$(function() {
  let parser = new DOMParser();

  let parentNode = document.getElementById('popular-list');
  // The code below generates the html that gives the user options for different
  // popular locations
  state.allLocations.forEach(function(option, i) {
    let checked = (i == 1) ? 'checked' : '';
    let html = parser.parseFromString(`
      <div onclick="selectLocation(this)" class="card text-center ${checked}">
        <img class="location-image" src="assets/${option.image}">
        <label for="${option.name}">${option.label}</label>
        <input type="radio" name="location" ${checked} value="${option.name}">
      </div>`, 'text/html').body.firstChild;
    parentNode.append(html);
  });

  function resize(asset, width, height) {
    if( height * (1920/756) > width) {
      asset.style.height = '100%';
    } else {
      asset.style.width = '100%';
    }
  }

  // The event handler below handles the user uploading new files
  uploadInput = document.getElementById('image-upload');
  uploadInput.addEventListener('change', function() {
    var container = $(".preview-holder");
    container.empty();

    addtime(false);
    Array.prototype.slice.call(uploadInput.files).forEach(function(file) {

      let reader = new FileReader();

      reader.onload = function(e) {
        var asset;

        let row = $(
          ['<div class="screen">',
             '<img src="assets/screen-black.png" class="bg">',
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

    $("#upload-holder label").html("Change Assets");
  });

  paypal.Button.render({
      env: 'sandbox', // sandbox | production
      // Create a PayPal app: https://developer.paypal.com/developer/applications/create
      client: {
        sandbox: 'ARrHtZndH9dLcfMG3bzxFAAtY6fCZcJ7EZcPzdDZ9Zg5tPznHAN2TTEoQ0rL_ijpDPOdzvPhMnayZf4p',
        // A valid key will need to be added below for payment to work in production
        production: '<insert production client id>',
      },
      // Show the buyer a 'Pay Now' button in the checkout flow
      commit: true,
      // payment() is called when the button is clicked
      payment: (data, actions) => {
        // Make a call to the REST api to create the payment
        create_campaign(actions);
      },
      // onAuthorize() is called when the buyer approves the payment
      onAuthorize: (data, actions) => {
        // Make a call to the REST api to execute the payment
        // This happens when the payment to paypal is completed 
        return actions.payment
          .execute()
          .then(() => {
            return actions.payment.get().then(order => {
              axios({
                method: 'put',
                url: '/api/campaign',
                data: {
                  campaignId: state.campaign_id,
                  payer: order.payer, //JSON.stringify(order.payer),
                  paymentInfo: data //JSON.stringify(data),
                },
              }).then(response => {
                console.log(response);
                window.location = response.data.location;
              });
            });
          })
          .catch(e => console.log('error in request: ', e));
      },
    },
    '#paypal-button-container',
  );
});
