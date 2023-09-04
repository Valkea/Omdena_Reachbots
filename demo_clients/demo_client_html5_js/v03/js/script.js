
// --- GLOBAL VARIABLES ---

// const api_url = "http://ec2-54-74-190-190.eu-west-1.compute.amazonaws.com:5000/";
const api_url = "http://127.0.0.1:5000/";

var winW = window.innerWidth;
var winH = window.innerHeight;

// --- INIT ---

window.onload = function() {

	var fileList = [];
	function go(evnt){
		if (fileInput.files.length > 0) {
			fileList = [];
			for (var i = 0; i < fileInput.files.length; i++) {
				fileList.push(fileInput.files[i]);
			}
			console.log(fileList);
			display_originals(fileList);
			predict_all(fileList)
		}
	}

	var fileInput = document.getElementById('filesupload');
	fileInput.addEventListener('change', go);

	var showlabels = document.getElementById('show_labels');
	showlabels.addEventListener('change', go);
}

// --- FUNCTIONS

const RETRY_COUNT = 5;
async function fetchRetry(...args) {
	let count = RETRY_COUNT;
  	while(count > 0) {
    		try {
      			return await fetch(...args);
    		} catch(error) {
			console.error('error:', error)
		}
    		count -= 1;
  	}

	throw new Error(`Too many retries`);
}

function display_originals( files ){

	var div_original = document.getElementById('originals');
	div_original.innerHTML = ""

	let i = 0;
	for (var file of files){
		var img_thumb = document.createElement("img")
		img_thumb.id = "thumb"+i
		img_thumb.classList.add('thumb');
        	img_thumb.src=URL.createObjectURL(file);
		div_original.appendChild(img_thumb);

		var img_original = document.createElement("img")
		img_original.id = "original"+i
		img_original.classList.add('original');
        	img_original.src=URL.createObjectURL(file);
		div_original.appendChild(img_original);

		i++;
		
		console.log(file)
	}
}


function predict_all(files){
 	var div_results = document.getElementById('all_results');
	div_results.innerHTML = ""

	predict_dmg_loop(files, 0)
}

function predict_dmg_loop(files, index=0){
     	postPicture(index, files, "predict_defects", saveJson)
}

function postPicture(index, files, action, callback) {

	console.log("postPictures:"+index+" / "+action)
   
	let formData = new FormData();
	formData.append("file", filesupload.files[index]);

	var myInit = {
		method: 'POST',
		headers: new Headers(),
	    	// cache: 'default',
	    	// mode: 'cors',
	    	body: formData
    	}

    	return fetchRetry( api_url+action, myInit )
    	.then( response => response.json() )
    	.then( json => callback(json, index, files, action) )
    	.catch( error => console.error('error:', error) );
}

let save_json = []
function saveJson(json, index, files, action){
	console.log("saveJson:"+index+" / "+action+" / "+index+" / "+(files.length-1))

	// Just in case we add extra endpoints later...
	switch(action){
		case "predict_defects":

			new_item = {
				'defects_json':json,
			}
			save_json[index] = new_item;

			// Move this bloc in last case if there are several cases...
			showResult(save_json[index], index)
			if(index < files.length-1){
				predict_dmg_loop(files, index+1)
			} else {
				console.log("END")
				console.log(save_json)
			}
			break;
	}
}

function showResult( jsons, index ){

	var source = document.getElementById('blueprint')
	let new_element = source.cloneNode(true)
	new_element.id = "block"+index

 	var div_results = document.getElementById('all_results')
	div_results.appendChild(new_element)

	var canvas = new_element.getElementsByTagName("canvas")
    	ctx_dmg = canvas[0].getContext('2d')
	ctx_dmg.fillStyle = "#FF0000";
	ctx_dmg.fillRect(2, 2, 10, 10)
	newW = Math.min(winW/2,600)
 	drawCanvas(canvas[0], index, newW, newW, jsons);

	var result_cell = new_element.getElementsByClassName('result')
	addBullets(result_cell[0], jsons)

	var jsons_cell = new_element.getElementsByClassName('jsons')
	output_jsons = "<h3>Defects JSON</h3>"+JSON.stringify(jsons['defects_json'])
	jsons_cell[0].innerHTML = output_jsons
}

function addBullets(result_cell, jsons){

	var i = 0
 	for(let defect of jsons['defects_json'].defects){

		result = "<h3>Defect "+i+"</h3><ul>"
		for (const [key, value] of Object.entries(defect)) {
			if( ["probability", "type"].includes(key) ){
				result += "<li><strong>"+key+":</strong> "+value+"</li>";
			}
		}

		result += "</ul>"

		result_cell.innerHTML += result
		i++
	}
}

function drawCanvas(canvas, index, newWidth, newHeight, jsons) {

	var showlabels = document.getElementById('show_labels').checked;
 	var image = document.getElementById('original'+index);

	canvas.width = newWidth;
        canvas.height = newHeight;

	ratioW = newWidth/image.width;
	ratioH = newHeight/image.height;

    	ctx = canvas.getContext('2d');

        // --- DRAW THE IMAGE
        ctx.drawImage(image, 0, 0, newWidth, newHeight);


	// --- DRAW DAMAGES 

 	// colors = [
 	// 	'#FF0000', // RED
 	// 	'#0000FF', // BLUE
 	// 	'#FF00FF', // MAGANTA
 	// 	'#FFC000', // ORANGE
 	// 	'#00CC00', // GREEN
 	// 	'#FFFC00', // YELLOW
 	// 	'#00FFFF', // CYAN
 	// ]

	colors = {
        	"spatter":		'#FF0000', // 921619 ~RED
        	"porosity": 		'#FFEC00', // c6b80c ~YELLOW
        	"irregular_bead":	'#0000FF', // 095d87 ~BLUE
        	"burn_through":		'#00BC5D', // 09703c ~GREEN
        	"undercut":		'#99B410', // 7f8d36 ~YELLOW/GREEN
        	"slag":			'#00FFFF', // 99b410 ~CYAN
        	"arc_strike":		'#C631C9', // c631c9 ~MAGENTA
        	"cracks": 		'#C4ACB4', // c4acb4 ~GREY
        	"start_stop": 		'#E6A22A', // 917b54 ~GOLD
        	"start_stop_overlap": 	'#E6A22A', // 917b54 ~GOLD /!\ OLD Label
        	"overlap": 		'#0B6B5F', // 09443d ~DARK GREEN
        	"gap":	 		'#0B6B5F', // 09443d ~DARK GREEN /!\ OLD Label
        	"others_not_classified":'#0B6B5F', // 0b6b5f ~ORANGE
        	"toe_angle": 		'#327A71', // 09443d ~DARK GREEN
	}
 
 
 	let i = 0
 	for(let defect of jsons['defects_json'].defects){
 
 		x = (defect.coords[0])*ratioW;
 		y = (defect.coords[1])*ratioH;
 		w = (defect.coords[2]-defect.coords[0])*ratioW;
 		h = (defect.coords[3]-defect.coords[1])*ratioH;
 
		// color = colors[i % colors.length]
		color = colors[defect.type]
 
 		ctx.beginPath();
 		ctx.rect(x, y, w, h)
 		ctx.strokeStyle = color;
 		ctx.stroke();
 
 		ctx.globalAlpha = 0.1;
 		ctx.fillStyle = "white";
 		ctx.fillRect(x, y, w, h);
 		ctx.globalAlpha = 1.0;
 
 		ctx.font = "10px Arial";
 		ctx.textAlign = "left";
	 	txt = i;
		if (showlabels == true){
	 		txt += " "+defect.type;
		}
 		let width = ctx.measureText(txt).width;
 
 		ctx.fillStyle = "white";
 		ctx.fillRect(x, y-15, width+10, 15);
 
 		ctx.fillStyle = color;
 		ctx.fillText(txt, x+5, y-5);
 		i++;
 	}
}
