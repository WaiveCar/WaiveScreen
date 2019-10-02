function renderScreen(screen) {
  const screenTitle = document.getElementById('screen-title');
  screenTitle.textContent = `Screen ${screen.id} Info`;
  fetch(`https://geocode.xyz/${screen.lat},${screen.lng}?geoit=json`)
    .then(resp => resp.json())
    .then(json => {
      const details = document.querySelector('.screen-details');
      details.innerHTML = `
        <div class="d-flex justify-content-between mt-4">
          <img src="/static/assets/screen_image.jpg" }}> 
          <div class="screen-details-text"> 
            <div class="d-flex">
              <div class="left col-5">
                <div>
                  Resolution
                </div>
                <div>
                  Type
                </div>
                <div>
                  Stationary
                </div>
                <div>
                  Location
                </div>
                <div>
                  Measurements
                </div>
                <div>
                  Busy Times
                </div>
              </div>
              <div class="right">
                <div>
                  1920 x 720
                </div>
                <div>
                  Car Screen
                </div>
                <div>
                  No
                </div>
                <div>
                  ${json.stnumber} ${json.staddress}
                </div>
                <div>
                  52.3" x 29.4"
                </div>
                <div>
                </div>
              </div>
            </div>
            <div>
              <img src="/static/assets/busy_times.png" }}>
            </div>
          </div>
        </div>
  `;
    })
    .catch(e => console.log('error: ', e));
}

function update_screen(el) {
  console.log(el);
}
function toggleEditor() {
  document.getElementsByClassName('editor')[0].classList.toggle('show');
}

(() => {
  $('input[value="no"]')
    .prop('checked', true)
    .parent()
    .addClass('selected');
  var e = Engine({container: document.getElementById('screen')});
  $('input[type=radio]').change(function() {
    console.log(this.name);
    e.Widget[this.name](this.value != 'no');
    $(`input[name=${this.name}]`)
      .parent()
      .removeClass('selected');
    this.parentNode.classList.add('selected');
  });
  const id = new URL(location.href).searchParams.get('id');
  fetch(`http://waivescreen.com/api/screens?id=${id}`)
    .then(response => response.json())
    .then(json => renderScreen(json[0]))
    .catch(e => console.log('error fetching screens', e));
})();
