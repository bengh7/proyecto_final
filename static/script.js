//Borrar el mensaje flash después de 7 segundos
//y añadir la clase fade para que se desvanezca

setTimeout(function(){
    var flash = document.getElementById('flash-message');
    
    if (flash) {
        flash.classList.remove('show');
        flash.classList.add('fade');
        setTimeout(()=> flash.remove(), 500); // Espera 0.5 sergundos antes de eliminar el elemento
    }   

}, 5000); // Espera 5 segundos antes de eliminar el elemento
