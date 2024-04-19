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

	/*
	// Alternative using the ON CHANGE events.
	
	var fileList = [];
	function go(evnt){
		if (fileInput.files.length > 0) {
			fileList = [];
			for (var i = 0; i < fileInput.files.length; i++) {
				fileList.push(fileInput.files[i]);
			}
			display_originals(fileList);
			// initializeCells(fileList);
			predict_all(fileList)
		}
	}

	var fileInput = document.getElementById('filesupload');
	fileInput.addEventListener('change', go);

	var showlabels = document.getElementById('show_labels');
	showlabels.addEventListener('change', go);

	var showresults = document.getElementById('show_results');
	showresults.addEventListener('change', go);
	*/

	// Alternative using SUBMIT button instead of auto submit.

	function go(evnt){
		fileList = [];
		for (var i = 0; i < fileInput.files.length; i++) {
			fileList.push(fileInput.files[i]);
		}
		display_originals(fileList);
	}
	var fileInput = document.getElementById('filesupload');
	fileInput.addEventListener('change', go);

	function predict(evnt){
		// initializeCells(fileList);
		predict_all(fileList)
	}
	var submitBtn = document.getElementById('predict');
	submitBtn.addEventListener('click', predict);

	document.querySelectorAll("input[name='model_type']").forEach((input) => {
        	input.addEventListener('change', populateModels);
    	});

	getModels(getModelsCallback, 'photo')
	var modelSelect = document.getElementById('model_select');
	modelSelect.addEventListener('change', go);

	initializeInputs()
}

// --- FUNCTIONS


function populateModels(evt){
	var model_type = event.target.value
	getModels(getModelsCallback, model_type)
	// go()
	initializeInputs(model_type)
}

function initializeInputs(model_type)
{
	let cell_showlabels = document.getElementById('show_labels_span');
	// let cell_showresults = document.getElementById('show_results');
	let cell_slide_step = document.getElementById('slide_step_span');
	let cell_min_defects = document.getElementById('min_defects_span');
	let cell_binary_threshold = document.getElementById('binary_threshold_span');
	let cell_multi_threshold = document.getElementById('multi_threshold_span');

	if (model_type == "laser"){
		cell_showlabels.style.display = "none";
		cell_slide_step.style.display = "block";
		cell_min_defects.style.display = "block";
		cell_binary_threshold.style.display = "block";
		cell_multi_threshold.style.display = "block";
	} else {
		cell_showlabels.style.display = "block";
		cell_slide_step.style.display = "none";
		cell_min_defects.style.display = "none";
		cell_binary_threshold.style.display = "block";
		cell_multi_threshold.style.display = "block";
	}
	
}

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

	// -- remove old options
	select.options.length = 0;

	// -- add new options
	for(const key in available_models){
		select.add(new Option(available_models[key]+" ["+key+"]", key, true), undefined);
		if (key == current_model){
			select.selectedIndex = count
		}
		count ++

	}
}

function getModels(callback, model_type) {

	if (model_type == 'laser'){
		action = "get_available_laser_models"
	} else {
		action = "get_available_photo_models"
	}

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

function cleanCells()
{
 	var div_results = document.getElementById('all_results')
	div_results.innerHTML = ""

	var jsons_cell = document.getElementById('json_result')
	jsons_cell.innerHTML = ""

	var time_cell = document.getElementById('time')
	time_cell.innerHTML = ""
}

let contexts = {}
function initializeCells(files, max_size=0){

	var source = document.getElementById('blueprint')
 	var div_results = document.getElementById('all_results')
	div_results.innerHTML = ""
	newW = Math.min(winW/2,600)
	newW = 200

	contexts = {}

	for(const i in files){

		if ((max_size > 0) && (i >= max_size)){
			console.log("OUT ON CLEAN")
			break
		}

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
	// initializeCells(files, max_size=0);

	cleanCells()

	let cell_status = document.getElementById('status')
	cell_status.innerHTML = "<b>PROCESSING</b><br><span class='loader'></span>"

     	await postPictures(files, "predict_defects", saveJson)
	showResult(files, save_json)
}

function isLaserModel() {
	var ele = document.getElementsByName('model_type');
	var value = undefined

        for (i = 0; i < ele.length; i++) {
         	if (ele[i].checked)
			value = ele[i].value;
        }
	return value == 'laser'
}

function postPictures(files, action, callback) {

	let formData = new FormData();
	for (const file of files) {
    		formData.append('file', file, file.name);
  	}

	let model_select_value = document.getElementById('model_select').value;
	let model_select_laser = isLaserModel();
	let binary_threshold_v = document.getElementById('binary_threshold').value;
	let multi_threshold_v = document.getElementById('multi_threshold').value;

	formData.append('selected_model', model_select_value);
	formData.append('laser_cut_image', model_select_laser);
	formData.append('binary_threshold', binary_threshold_v);
	formData.append('multi_threshold', multi_threshold_v);

	if (model_select_laser == true){

		slide_step_v = document.getElementById('slide_step').value;
		min_defects_v = document.getElementById('min_defects').value;

		formData.append('slide_step', slide_step_v);
		formData.append('min_defects', min_defects_v);

		action = "predict_laser_defects"
	} else {
		action = "predict_photo_defects"
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
		case "predict_laser_defects":
		case "predict_photo_defects":

			new_item = {
				'defects_json':json,
			}
			save_json = new_item;
			break;
	}
}


function showResult( files, jsons ){

	var cell_status = document.getElementById('status')
	const error = jsons['defects_json']['error_msg']

	if(error){
		console.log("ERROR")
		cell_status.innerHTML = "<b>STATUS:</b> ERROR > "+error
		return
	} else {
		cell_status.innerHTML = "<b>STATUS:</b> OK"
	}

	if(isLaserModel()){
		showLaserResult(files, jsons)
	} else {
		showPhotoResult(files, jsons)
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

var status_icon = {
	true:'🔴', false:'🟢', 'object':'🔴', 'string':'🟢', 'undefined':'⚪', 'no_pred':'⚪'
}

function showLaserResult( files, jsons ){

	const display_nodes_multi = ['probability', 'type', 'score', 'has_defect']
	const display_nodes_binary = ['probability', 'file', 'has_defect']

	const results = jsons['defects_json']['results']
	const max_cells = results.length
	initializeCells(files, max_cells)

	let cell_index = 0
	for(const result of results){

		binary_results = result['binary_results']
		multi_results = result['multi_results']

		// --- PART 1
		// last_img_index = multi_results['indexes'][0]
		last_img_index = cell_index
		cellref = files[last_img_index]
		let div_source = document.getElementById("block_"+cellref.name);

		// -- Display one image from the batch
		let loader_div = div_source.getElementsByClassName("loader");
		loader_div[0].style.display = 'none';

		let canvas_div = div_source.getElementsByClassName("canvas");
		canvas_div[0].style.display = 'block';

		let canvas = div_source.getElementsByTagName("canvas")
		newW = Math.min(winW/2,600)
		drawContextBackground(canvas[0], cellref.name, newW, newW);

		let result_show_cell = div_source.getElementsByClassName('result_show')
		let result_hide_cell = div_source.getElementsByClassName('result_hide')

		// -- Add classifiers status
		let has_defect_binary = false
		for(node of binary_results){
			if (eval(node['has_defect']) == true){
				has_defect_binary = true
				break
			}
		}
		let has_defect_multi = eval(multi_results['has_defect'])
		let used_multi = multi_results['type'] != 'no_pred'

		let multi_status
		switch (multi_results['type']) {
			case 'no_defect_found':
				multi_status = false
		    		break;
			case 'no_pred':
				multi_status = undefined
				break;
			default:
				multi_status = true
		}

		var status_str = "BINARY Classifier: "+status_icon[has_defect_binary]+" | "
		status_str += "MULTILABEL Classifier: "+status_icon[multi_status]+ "<br><br>"

		result_show_cell[0].innerHTML = status_str + result_show_cell[0].innerHTML
		result_hide_cell[0].innerHTML = status_str + result_hide_cell[0].innerHTML

		// -- Parse json

		if (multi_status != undefined ){
			addBulletMeta(result_show_cell[0], multi_results, "Multi model results", display_nodes_multi)
		}
		for( i in binary_results){
			addBulletMeta(result_show_cell[0], binary_results[i], "Binary model results "+i, display_nodes_binary)
		}

		cell_index++;
	}
}

function showPhotoResult( files, jsons ){

	const display_nodes_binary = ['probability', 'type', 'file', 'score', 'has_defect']
	const display_nodes_multi = ['probability', 'type']

	const results = jsons['defects_json']['results']
	const max_cells = results.length
	initializeCells(files, max_cells)
	
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

		for(const result of results){
			if(result.file == file.name)
			{
				var div_source = document.getElementById("block_"+file.name);
				var result_show_cell = div_source.getElementsByClassName('result_show')
				var result_hide_cell = div_source.getElementsByClassName('result_hide')
				addBulletMeta(result_show_cell[0], result, "Binary model results", display_nodes_binary)


				// Add classifiers status
				var has_defect_binary = result['has_defect']
				var has_defect_multil = ('defect_list' in result) && (typeof result['defect_list'] === 'object')

				var status_str = "BINARY Classifier: "+status_icon[has_defect_binary]+" | "
				status_str += "MULTILABEL Classifier: "+status_icon[typeof result['defect_list']]+ "<br><br>"

				result_show_cell[0].innerHTML = status_str + result_show_cell[0].innerHTML
				result_hide_cell[0].innerHTML = status_str + result_hide_cell[0].innerHTML

				var canvas = div_source.getElementsByTagName("canvas")
				newW = Math.min(winW/2,600)
				drawContextStatus(canvas[0], file.name, has_defect_binary, has_defect_multil, newW, newW);

				// Skip the drawing part if there is no defect
				if (!('defect_list' in result)){
					continue
				}

				const defect_list = result.defect_list

				if (typeof defect_list === "string"){
					result_show_cell[0].innerHTML += defect_list
					continue
				}

				for(const j in defect_list){
					defect = defect_list[j]

					let keys = ['probability', 'type', 'file', 'score', 'has_defect']
					addBulletMeta(result_show_cell[0], defect, "Multi model results "+j, display_nodes_multi)
					//addBulletDefects(result_show_cell[0], defect, i)
					if ('coords' in defect){
						drawContextDefect(file.name, defect, i);
					}
					i++;
				}
			}
		}
	}
}

function addBulletMeta(result_cell, defect, title, keys ){

	result = "<h3>"+title+"</h3><ul>"
	for (const [key, value] of Object.entries(defect)) {
		if( keys.includes(key) ){
			result += "<li><strong>"+key+":</strong> "+value+"</li>";
		}
	}

	result += "</ul>"
	result_cell.innerHTML += result
}
/*
function addBulletDefects(result_cell, defect, title, index){

	result = "<h3>"+title+" "+index+"</h3><ul>"
	for (const [key, value] of Object.entries(defect)) {
		if( ['probability', 'type'].includes(key) ){
			result += "<li><strong>"+key+":</strong> "+value+"</li>";
		}
	}

	result += "</ul>"
	result_cell.innerHTML += result
}
*/
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

function drawContextStatus(canvas, name, bin_status, multi_status, newWidth, newHeight)
{
	if (bin_status == true && multi_status == true){
		status_color = "#FF0000"
	} else if (bin_status == true && multi_status == false){
		status_color = "#FFAA00"
	} else {
		status_color = "#00FF00"
	}

 	let image = document.getElementById('original_'+name);
	let ctx = contexts[name];

 	ctx.beginPath();
 	ctx.rect(0, 0, newWidth, newHeight)
 	ctx.strokeStyle = status_color;
	ctx.lineWidth = 5;
 	ctx.stroke();
	ctx.lineWidth = 1;
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
