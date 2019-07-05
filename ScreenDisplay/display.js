window.onload = function init() {
  self.ads = Engine({
    server: 'http://localhost:4096/'
  });
  ads.on('system', function(data) {
    document.getElementsByClassName('info')[0].innerHTML = [data.number.slice(-7), data.uuid.slice(5)].join(' ');
  });
  ads.Start();
}
