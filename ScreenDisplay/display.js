window.onload = function init() {
  self.ads = Engine({
    server: 'http://localhost:4096/'
  });
  ads.Start();
}
