function selectLocation(what) {
  $(what).siblings().removeClass('checked');
  $(what).addClass('checked');
  $("input", what).prop('checked', true);
}

window.fakebuy = function () {
  console.log($(document.forms[0]).serializeArray());
}

$(function() {
  function price(amount) {
    return '$' + (parseInt(amount, 10)/100).toFixed(2);
  }
  // This 'state' is used to store anything that is needed within this scope
  let state = {};
  let parser = new DOMParser();
  let sessionId = sessionStorage.getItem('sessionId');
  // This call to the api fetches the locations that are currently popular and sends the
  // sessionId/quoteId if there is one. The sessionId is not currently used here, but is
  // used by the server and could be used to reload previous inputs by the user. These previous
  // inputs are already cached by the server
  axios
    .get('/splash_resources', sessionId && {headers: {'Session-Id': sessionId}})
    .then(response => {
      if (response.headers['session-id'] !== sessionId) {
        sessionStorage.setItem('sessionId', response.headers['session-id']);
      }
      state.allLocations = response.data.popularLocations.concat(
        response.data.cheapLocations,
      );
      let parentNode = document.getElementById('popular-list');
      // The code below generates the html that gives the user options for different
      // popular locations
      response.data.popularLocations.forEach((option, i) => {
        let checked = (i == 1) ? 'checked' : '';
        let html = parser.parseFromString(
          `
      <div onclick="selectLocation(this)" class="card text-center ${checked}">
        <img class="location-image" src="assets/${option.image}">
        <label for="${option.name}">${option.label}</label>
        <input type="radio" name="location" ${checked} value="${option.name}">
      </div>`,
          'text/html',
        ).body.firstChild;
        parentNode.append(html);
      });
    })
    .catch(err => {
      console.log('error: ', err);
    });

  // The event handler below handles the user uploading new files
  let uploadInput = document.getElementById('image-upload');
  uploadInput.addEventListener('change', () => {
    let reader = new FileReader();
    reader.onload = e => {
      let previewImage = document.getElementById('preview-image');
      previewImage.src = e.target.result;
      previewImage.style.visibility = 'visible';
      $("#upload-holder label").html("Change Image");
    };
    reader.readAsDataURL(uploadInput.files[0]);
  });

  paypal.Button.render(
    {
      env: 'sandbox', // sandbox | production
      // Create a PayPal app: https://developer.paypal.com/developer/applications/create
      client: {
        sandbox:
        // Currently, this is a code for my personal paypal account and definitely will need to be changed
          'ARrHtZndH9dLcfMG3bzxFAAtY6fCZcJ7EZcPzdDZ9Zg5tPznHAN2TTEoQ0rL_ijpDPOdzvPhMnayZf4p',
        // A valid key will need to be added below for payment to work in production
        production: '<insert production client id>',
      },
      // Show the buyer a 'Pay Now' button in the checkout flow
      commit: true,
      // payment() is called when the button is clicked
      payment: (data, actions) => {
        // Before the payment is processed by paypal, a user's purchase is sent to the server with 
        // the information that has so far been obtained including the picture.
        let formData = new FormData();
        formData.append('file', uploadInput.files[0]);
        formData.append('cart', JSON.stringify(state.selectedCart));
        formData.append('quoteId', sessionStorage.getItem('sessionId'));
        return axios({
          method: 'post',
          url: '/capture',
          data: formData,
          config: {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          },
        }).then(resp => {
          // Make a call to the REST api to create the payment
          return actions.payment.create({
            payment: {
              transactions: [
                {
                  amount: {
                    total: String(
                      (state.selectedCart.total / 100).toFixed(2),
                    ),
                    currency: 'USD',
                  },
                },
              ],
            },
          });
        });
      },
      // onAuthorize() is called when the buyer approves the payment
      onAuthorize: (data, actions) => {
        // Make a call to the REST api to execute the payment
        // This happens when the payment to paypal is completed 
        return actions.payment
          .execute()
          .then(() => {
            return actions.payment.get().then(order => {
              // Once the payment is completed, the payment information is fetched and then sent to the server
              // so that it can be stored in the database for future use
              let formData = new FormData();
              formData.append('file', uploadInput.files[0]);
              formData.append(
                'cart',
                JSON.stringify(state.selectedCart),
              );
              formData.append('payer', JSON.stringify(order.payer));
              formData.append('paymentInfo', JSON.stringify(data));
              axios({
                method: 'put',
                url: '/capture',
                data: {
                  quoteId: sessionStorage.getItem('sessionId'),
                  payer: JSON.stringify(order.payer),
                  paymentInfo: JSON.stringify(data),
                },
              }).then(response => {
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
