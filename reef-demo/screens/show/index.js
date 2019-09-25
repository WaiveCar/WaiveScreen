function renderScreen(screen) {
  const screenTitle = document.getElementById('screen-title');
  screenTitle.textContent = `Screen ${screen.id} Info`;
  fetch(`https://geocode.xyz/${screen.lat},${screen.lng}?geoit=json`)
    .then(resp => resp.json())
    .then(json => {
      console.log(json);
      const details = document.querySelector('.screen-details');
      details.innerHTML = `
        <div class="d-flex justify-content-around mt-4">
          <img src="/screen_image.jpg"> 
          <div class="screen-details-text d-flex flex-column justify-content-around"> 
            <div class="d-flex justify-content-between">
              <div class="left">Resolution</div>
              <div class="right">1920 x 720</div>
            </div>
            <div class="d-flex justify-content-between">
              <div class="left">Type</div>
              <div class="right">Car Screen</div>
            </div>
            <div class="d-flex justify-content-between">
              <div class="left">Location</div>
              <div class="right">${json.stnumber} ${json.staddress}</div>
            </div>
            <div class="d-flex justify-content-between">
              <div class="left">Measurements</div>
              <div class="right">52.3" x 29.4"</div>
            </div>
            <div class="d-flex justify-content-center">
              <img src="/busy_times.png">
            </div>
          </div>
        </div>
  `;
    })
    .catch(e => console.log('error: ', e));
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
