
// --- GLOBAL VARIABLES ---

// const api_url = "http://ec2-54-74-190-190.eu-west-1.compute.amazonaws.com:5000/";
const api_url = "http://127.0.0.1:5000/";
let ctx = undefined;

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
	var image = document.getElementById('output');

	switch (callback_id){
		case "result_defects":

			var show_json = document.getElementById('show_defects_json');
			show_json.innerHTML = "<h2>JSON</h2>"+myObj;

			drawDefects(image, 200, 200, json.defects);

			var result_cell = document.getElementById('result_defect')
			result_cell.innerHTML = "<h2>Defects</h2>"

			var i = 0
			for(let defect of json.defects){

				result = "<h3>"+i+"</h3><ul>"
				for (const [key, value] of Object.entries(defect)) {
					result += "<li><strong>"+key+":</strong> "+value+"</li>";
				}
				result += "</ul>"

				result_cell.innerHTML += result
				i++
			}

			break;
	}
}

function drawDefects(image, newWidth, newHeight, defects) {

    	//create an image object from the path
    	const originalImage = new Image();
    	originalImage.src = image.src;

    	const canvas = document.getElementById('canvas_defects');
    	ctx_defect = canvas.getContext('2d');

        canvas.width = image.width;
        canvas.height = image.height;

        //draw the image
        ctx_defect.drawImage(originalImage, 0, 0, image.width, image.height);

	colors = [
		'#FF0000', // RED
		'#0000FF', // BLUE
		'#FF00FF', // MAGANTA
		'#FFC000', // ORANGE
		'#00CC00', // GREEN
		'#FFFC00', // YELLOW
		'#00FFFF', // CYAN
	]


	let i = 0
	for(let defect of defects){

		x = defect.coords[0]
		y = defect.coords[1]
		w = defect.coords[2]-defect.coords[0]
		h = defect.coords[3]-defect.coords[1]

		color = colors[i % colors.length]

		ctx_defect.beginPath();
		ctx_defect.rect(x, y, w, h)
		ctx_defect.strokeStyle = color;
		ctx_defect.stroke();

		ctx_defect.globalAlpha = 0.1;
		ctx_defect.fillStyle = "white";
		ctx_defect.fillRect(x, y, w, h);
		ctx_defect.globalAlpha = 1.0;

		ctx_defect.font = "10px Arial";
		ctx_defect.textAlign = "left";
		txt = i+" "+defect.type;
		let width = ctx_defect.measureText(txt).width;

		ctx_defect.fillStyle = "white";
		ctx_defect.fillRect(x, y, width+10, 15);

		ctx_defect.fillStyle = color;
		ctx_defect.fillText(txt, x+5, y+10);
		i++;
	}
}

function cropImage(imagePath, canvasTarget, newX, newY, newWidth, newHeight) {

    	//create an image object from the path
    	const originalImage = new Image();
    	originalImage.src = imagePath;

    	//initialize the canvas object
    	const canvas = document.getElementById(canvasTarget);
	if(ctx === undefined){
    		ctx = canvas.getContext('2d');
	};

        //set the canvas size to the new width and height
        canvas.width = newWidth;
        canvas.height = newHeight;

        //draw the image
        ctx.drawImage(originalImage, newX, newY, newWidth, newHeight, 0, 0, newWidth, newHeight);
}

function onLoadImage() {
	var image = document.getElementById('output');
        image.src=URL.createObjectURL(event.target.files[0]);
	// cropImage(image.src, 0, 0, 200, 200);
}
