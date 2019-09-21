function login() {
  let form = document.querySelector('form');
  let data = new FormData(form);
  let object = {};
  data.forEach((value, key) => {
    object[key] = value;
  });
  let json = JSON.stringify(object);
  console.log(json);
}
