function newRow(el, dataName){
    inputSet = el.parentElement;
    nextRowId = el.getAttribute("nextRow");
    if(nextRowId == "0"){
        nextRowId = 1
    }
    el.setAttribute("nextRow", parseInt(nextRowId) + 1);
    row0 = document.getElementsByName(dataName + "row0")[0];
    rowN = row0.cloneNode(true);
    rowN.setAttribute("name", nextRowId)
    for(child of rowN.children){
        if(child.classList.contains("mb-3")){
            input = child.children[1].children[0];
            input.name = input.name.split('-')[0] + '-' + nextRowId;
            input.setAttribute("value", "")
        }
    }
    rowN.children[0].name = rowN.children[0].name.split('-')[0] + '-' + nextRowId;
    rowN.children[0].setAttribute("value", "")
    inputSet.insertBefore(rowN, el);
}