function renderScreen(screen) {
  const screenTitle = document.getElementById('screen-title');
  screenTitle.textContent = `Screen ${screen.id} Info`;
}

function toggleEditor() {
  document.getElementsByClassName('editor')[0].classList.toggle('show');
}

(() => {
  $('input[value="no"]').prop('checked', true).parent().addClass('selected');
  $("input[type=radio]").change(function(){
    $(`input[name=${this.name}]`).parent().removeClass('selected');
    this.parentNode.classList.add('selected');
  });
  const id = new URL(location.href).searchParams.get('id');
  fetch(`http://waivescreen.com/api/screens?id=${id}`)
    .then(response => response.json())
    .then(json => renderScreen(json[0]))
    .catch(e => console.log('error fetching screens', e));
})();
