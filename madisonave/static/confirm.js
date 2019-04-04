(function() {
  let parser = new DOMParser();
  let cart = null;
  let sessionId = sessionStorage.getItem('sessionId');
  // This api call fetches the cart from the server by sessionId. If there is no session or no valid session,
  // the user is redirected to the homepage. If there is one, a summary of what was ordered with it is rendered
  axios
    .get(
      '/prev_cart',
      sessionId && {
        headers: {'Session-Id': sessionId},
      },
    )
    .then(result => {
      cart = result.data;
      let html = parser.parseFromString(
        `
      <div class="container">
        <div class="text-center mt-5 mb-3">
          Thanks for purchasing advertising with Waive! A confrimation e-mail has been sent to ${
            cart.email
          }.
        </div>
        <table class="table table-bordered table-hover">
          <thead>
            <tr>
              <th scope="col" style="width: 20%">Item</th>
              <th scope="col" style="width: 20%">Price</th>
              <th scope="col" style="width: 20%">Quantity</th>
              <th scope="col" style="width: 20%">Total</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td scope="row">Extra Days</td>
              <td>$${(cart.pricePerDay / 100).toFixed(2)}</td>
              <td>
                ${cart.addedDays}
              </td>
              <td id="day-quantity-total">$${(
                cart.addedDays *
                cart.pricePerDay /
                100
              ).toFixed(2)}</td>
            </tr>
            <tr>
              <td scope="row">Extra Minutes Per Day</td>
              <td>$${(cart.perMinutePerDay / 100).toFixed(2)}</td>
              <td>
                ${cart.addedMinutes}
              </td>
              <td id="mins-quantity-total">$${(
                cart.addedMinutes *
                cart.perMinutePerDay *
                (cart.days + cart.addedDays) /
                100
              ).toFixed(2)}</td>
            </tr>
            <tr>
              <td>
                Total minutes per day: ${(
                  cart.addedMinutes +
                  cart.secondsPerDay / 60
                ).toFixed(2)}
              <td>
                Total cost per day: $${(
                  cart.total /
                  100 /
                  (cart.days + cart.addedDays)
                ).toFixed(2)}
              </td>
              </td>
              <td>
                Total days: ${cart.days + cart.addedDays}
              </td>
              <td>
                Total cost: $${(cart.total / 100).toFixed(2)}
              </td>
            </tr>
          </tbody>
        </table>
        <div class="text-center">
          Your advertisement will run between ${cart.start} and ${cart.end}
        </div>
      </div>`,
        'text/html',
      ).body.firstChild;
      document.getElementById('root').appendChild(html);
    })
    .catch(e => (window.location = '/'));
})();
