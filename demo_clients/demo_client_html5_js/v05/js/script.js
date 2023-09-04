/*
Description: This script provides a javascript interface connecting to the inference API (API_serving) to get defects from image(s) and video and display the result on the HTML page.
Author: Letremble Emmanuel (emmanuel+code@shedge.com)
Command: streamlit run app.py
*/


// --- GLOBAL VARIABLES ---

const currentUrl = window.location.href;
const splitUrl = currentUrl.split("5000");
// let api_url = "http://ec2-34-244-123-190.eu-west-1.compute.amazonaws.com:5000/";
let api_url = "http://127.0.0.1:5000/";

if(currentUrl != splitUrl){
	api_url = splitUrl[0]+"5000/"
}

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
			initializeCells(fileList);
			predict_all(fileList)
		}
	}

	var fileInput = document.getElementById('filesupload');
	fileInput.addEventListener('change', go);

	var showlabels = document.getElementById('show_labels');
	showlabels.addEventListener('change', go);

	var showresults = document.getElementById('show_results');
	showresults.addEventListener('change', go);


	/* # Alternative using SUBMIT button instead of auto submit.

	function go(evnt){
		fileList = [];
		for (var i = 0; i < fileInput.files.length; i++) {
			fileList.push(fileInput.files[i]);
		}
		console.log(fileList);
		display_originals(fileList);
	}
	var fileInput = document.getElementById('filesupload');
	fileInput.addEventListener('change', go);

	function predict(evnt){
		initializeCells(fileList);
		predict_all(fileList)
	}
	var submitBtn = document.getElementById('predict');
	submitBtn.addEventListener('click', predict);

	*/

	getModels(getModelsCallback)
	var modelselect = document.getElementById('model_select');
	modelselect.addEventListener('change', go);
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

function getModelsCallback(json) {

	available_models = json['available_models']
	current_model = json['current_model']

	var select = document.getElementById('model_select');
	let count = 0

	for(const key in available_models){
		select.options[count] = new Option(available_models[key]+" ["+key+"]", key, true);
		if (key == current_model){
			select.selectedIndex = count
		}
		count ++

	}
}

function getModels(callback) {

	action ="get_available_models"

	var myInit = {
		method: 'GET',
		headers: new Headers(),
	    	// cache: 'default',
	    	// mode: 'cors',
	    	// body: formData
    	}

    	return fetchRetry( api_url+action, myInit )
    	.then( response => response.json() )
    	.then( json => callback(json) )
    	.catch( error => console.error('error:', error) );
}


function display_originals( files ){

	var div_original = document.getElementById('originals');
	div_original.innerHTML = ""

	let i = 0;
	for (var file of files){
		var name = file.name

		var img_thumb = document.createElement("img")
		img_thumb.id = "thumb_"+name;
		img_thumb.classList.add('thumb');
        	img_thumb.src=URL.createObjectURL(file);
		div_original.appendChild(img_thumb);

		var img_original = document.createElement("img")
		img_original.id = "original_"+name;
		img_original.classList.add('original');
        	img_original.src=URL.createObjectURL(file);
		div_original.appendChild(img_original);

		i++;
		
		console.log(file)
	}
}

function toggleResults(block_name) {

 	var div_source = document.getElementById(block_name);
	var result_show_cell = div_source.getElementsByClassName('result_show')[0];
	var result_hide_cell = div_source.getElementsByClassName('result_hide')[0];

	if (result_show_cell.style.display === "none") {
		result_show_cell.style.display = "block";
		result_hide_cell.style.display = "none";
	} else {
		result_show_cell.style.display = "none";
		result_hide_cell.style.display = "block";
	}
}

let contexts = {}
function initializeCells(files){

	var source = document.getElementById('blueprint')
 	var div_results = document.getElementById('all_results')
	div_results.innerHTML = ""
	newW = Math.min(winW/2,600)
	newW = 200

	contexts = {}

	for(const i in files){

		var name = files[i].name
		let new_element = source.cloneNode(true)
		new_element.id = "block_"+name
		
		// Add toggle buttons
		var result_show_cell = new_element.getElementsByClassName('result_show');
		result_show_cell[0].innerHTML += "<button onclick='toggleResults(\""+new_element.id+"\")'>Hide results</button>"

		var result_hide_cell = new_element.getElementsByClassName('result_hide');
		result_hide_cell[0].innerHTML += "<button onclick='toggleResults(\""+new_element.id+"\")'>Show results</button>"

		showresults = document.getElementById('show_results').checked;
		if (showresults) {
			result_hide_cell[0].style.display = "none";
		} else {
			result_show_cell[0].style.display = "none";
		}

		// Save canvas to ctx to access it later
		var canvas = new_element.getElementsByTagName("canvas")
    		var ctx = canvas[0].getContext('2d');

		contexts[name] = ctx;

		div_results.appendChild(new_element)
	}
}

async function predict_all(files){
     	await postPictures(files, "predict_defects", saveJson)
	showResult(files, save_json)
}

function postPictures(files, action, callback) {

	let formData = new FormData();
	for (const file of files) {
    		formData.append('file', file, file.name);
  	}

	model_select_value = document.getElementById('model_select').value;
	if (model_select_value != ''){
		formData.append('selected_model', model_select_value);
	}

	var myInit = {
		method: 'POST',
		headers: new Headers(),
	    	// cache: 'default',
	    	// mode: 'cors',
	    	body: formData
    	}

    	return fetchRetry( api_url+action, myInit )
    	.then( response => response.json() )
    	.then( json => callback(json, files, action) )
    	.catch( error => console.error('error:', error) );
}


let save_json = []
function saveJson(json, files, action){
	console.log("saveJson:"+action+" / "+(files.length-1))

	switch(action){
		case "predict_defects":

			new_item = {
				'defects_json':json,
			}
			save_json = new_item;
			break;
	}
}


function showResult( files, jsons ){
	
	for(const file of files){
 		var div_source = document.getElementById("block_"+file.name);

		var loader_div = div_source.getElementsByClassName("loader");
		loader_div[0].style.display = 'none';

		var canvas_div = div_source.getElementsByClassName("canvas");
		canvas_div[0].style.display = 'block';

		var canvas = div_source.getElementsByTagName("canvas")
		newW = Math.min(winW/2,600)
		drawContextBackground(canvas[0], file.name, newW, newW);
	}

	for(const file of files){
		let i = 0
		for(const defect of jsons['defects_json']['defects']){
			if(defect.file == file.name)
			{
 				var div_source = document.getElementById("block_"+file.name);
				var result_cell = div_source.getElementsByClassName('result_show')

				addBulletDefects(result_cell[0], defect, i, defect.probable_duplicate)
				drawContextDefect(file.name, defect, i);

				i++;
			}
		}
	}
	var jsons_cell = document.getElementById('json_result')
	var jsons_str = JSON.stringify(jsons['defects_json'])
	var jsons_def = jsons['defects_json']
	jsons_cell.innerHTML = "<br><strong>Defects</strong><br>"+jsons_str

	var time_cell = document.getElementById('time')
	time_cell.innerHTML = "<br><strong>Total inference time:</strong> "
	time_cell.innerHTML += jsons['defects_json']['inference_time']
	time_cell.innerHTML += "<br><strong>Mean inference time:</strong> "
	time_cell.innerHTML += jsons['defects_json']['mean_inference_time']
}

function addBulletDefects(result_cell, defect, index, is_duplicate){

	var duplicate_text = (is_duplicate) ? " (probable duplicate)" : "";
	var duplicate_class = (is_duplicate) ? " class='duplicate'" : "";

	result = "<h3 "+duplicate_class+">Defect "+index+duplicate_text+"</h3><ul "+duplicate_class+">"
	for (const [key, value] of Object.entries(defect)) {
		if( ['probability', 'type', 'file'].includes(key) ){
			result += "<li><strong>"+key+":</strong> "+value+"</li>";
		}
	}

	result += "</ul>"
	result_cell.innerHTML += result
}

// --- DRAW DAMAGES & PLATES

/*colors = [
	'#FF0000', // RED
	'#0000FF', // BLUE
	'#FF00FF', // MAGANTA
	'#FFC000', // ORANGE
	'#00CC00', // GREEN
	'#FFFC00', // YELLOW
	'#00FFFF', // CYAN
]*/

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


function drawContextBackground(canvas, name, newWidth, newHeight)
{
 	let image = document.getElementById('original_'+name);
	let ctx = contexts[name];

	canvas.width = newWidth;
        canvas.height = newHeight;

	ctx.ratioW = newWidth/image.width;
	ctx.ratioH = newHeight/image.height;
	ctx.j = 0;

        ctx.drawImage(image, 0, 0, newWidth, newHeight);
}

function drawContextDefect(name, defect, i){

	let ctx = contexts[name];

	ctx.showlabels = document.getElementById('show_labels').checked;

 	x = (defect.coords[0])*ctx.ratioW;
 	y = (defect.coords[1])*ctx.ratioH;
 	w = (defect.coords[2]-defect.coords[0])*ctx.ratioW;
 	h = (defect.coords[3]-defect.coords[1])*ctx.ratioH;
 
 	if(defect.probable_duplicate == true){
 		ctx.setLineDash([3, 3]);
 		ctx.globalAlpha = 0.75;
 		color = "black";
 	} else {
 		ctx.setLineDash([]);
 		ctx.globalAlpha = 1.0;
 		// color = colors[ctx.j % colors.length];
		color = colors[defect.type];
 		ctx.j++;
 	}
 
 	ctx.beginPath();
 	ctx.rect(x, y, w, h)
 	ctx.strokeStyle = color;
 	ctx.stroke();
 
 	ctx.globalAlpha = 0.1;
 	ctx.fillStyle = "white";
 	ctx.fillRect(x, y, w, h);
 	ctx.globalAlpha = 1.0;
 
 	ctx.font = "10px bold Arial";
 	ctx.textAlign = "left";
	txt = i;
	if (ctx.showlabels == true){
		txt += " "+defect.type;
	}
 	let width = ctx.measureText(txt).width;
 
 	ctx.fillStyle = "white";
 	ctx.fillRect(x, y-15, width+10, 15);
 
 	ctx.fillStyle = color;
 	ctx.fillText(txt, x+5, y-5);
}
