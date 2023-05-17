document.addEventListener("DOMContentLoaded", function(event) { 
    var scrollpos = localStorage.getItem('scrollpos');
    if (scrollpos) window.scrollTo(0, scrollpos);    
});

window.onbeforeunload = function(e) {
    localStorage.setItem('scrollpos', window.scrollY);
};
function filtr(filtr, type){
    var cells = document.getElementsByName(type)
    cells.forEach(element => {
        if(element.innerHTML.toLowerCase().includes(filtr.toLowerCase())){
            element.parentElement.className = ""
        }
        else{
            element.parentElement.className = "d-none"
        }
    });
}