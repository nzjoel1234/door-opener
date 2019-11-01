
const d = document;

function getRequest(url, onFailure, onSuccess) {
    const request = new XMLHttpRequest();
    request.onreadystatechange = () => {
        if (request.readyState != 4) {
            return;
        }
        if (request.status !== 200) {
            onFailure(request);
            return;
        }
        onSuccess(request);
    }
    request.open('GET', url);
    request.send();
    return request;
}

function postJsonRequest(url, data, onFailure, onSuccess) {
    console.log('POST', { url, data });
    const request = new XMLHttpRequest();
    request.onreadystatechange = () => {
        if (request.readyState != 4) {
            return;
        }
        if (request.status !== 200) {
            onFailure(request);
            return;
        }
        onSuccess(request);
    }
    request.open('POST', url);
    if (data) {
        request.setRequestHeader("Content-type", "application/json");
        request.send(JSON.stringify(data));
    } else {
        request.send();
    }
    return request;
}

function addSelectOption(selectElement, label, value) {
    var optionEl = d.createElement('option');
    optionEl.setAttribute('value', value == null ? '' : value);
    optionEl.innerHTML = label;
    selectElement.appendChild(optionEl);
}
