
// --- GLOBAL VARIABLES ---

// const api_url = "http://ec2-54-74-190-190.eu-west-1.compute.amazonaws.com:5000/"
const api_url = "http://127.0.0.1:5000/";

// --- FUNCTIONS

function postPicture(url, callback_id) {
   
	let formData = new FormData();
    	formData.append("file", fileupload.files[0]);

	var myInit = {
		method: 'POST',
	    	headers: new Headers(),
	    	// cache: 'default',
	    	// mode: 'cors',
	    	body: formData
    	}

    	return fetch( url, myInit )
    	.then( response => response.json() )
    	.then( json => callback(json, callback_id) )
    	.catch( error => console.error('error:', error) );
}

function predict_defects() {

	url = api_url + "predict_defects"
	callback_id = 'result_defects'

    	postPicture(url, callback_id)
}

function callback(json, callback_id) {

	myObj = JSON.stringify(json);
	document.getElementById(callback_id).innerHTML = myObj;
}

