(() => {
  document.querySelector('.form-fields').innerHTML = [
    'email',
    'password',
  ]
    .map(
      field => {
        var type = field == 'email' ? 'text' : 'password';
        return `
    <div class="form-group">
      <input 
        name="${field}" 
        type="${type}" 
        class="form-control" 
        id="${field}" 
        placeholder="${`${field[0].toUpperCase() + field.slice(1)}`}" 
        autocomplete="off"
      >
    </div>
  
  `}
    )
    .join('');
})();
