from apiflask import APIFlask, Schema
from apiflask.fields import Integer, String, File, List, Nested, Boolean, Float
from apiflask.validators import Length, Range


# --- Define input and outputs for APIFlask documentation ---

class PhotoDefectsIn(Schema):
    file = List(File(required=True), dump_default=False)
    selected_model = String(required=True)
    binary_threshold = Float(validate=Range(0.0, 1.0), dump_default=False)
    multi_threshold = Float(validate=Range(0.0, 1.0), dump_default=False)

class LaserDefectsIn(Schema):
    file = List(File(required=True), dump_default=False)
    selected_model = String(required=True)
    slide_step = Integer(validate=Range(1,10), dump_default=False)
    min_defects = Integer(validate=Range(1,10), dump_default=False)
    binary_threshold = Float(validate=Range(0.0, 1.0), dump_default=False)
    multi_threshold = Float(validate=Range(0.0, 1.0), dump_default=False)


# class DefectsIn(Schema):
#     file = File(required=True)
#     selected_model = String(required=True)
#     laser_cut_image = Boolean()

damage_sample = [
    {
        "type": "irregular_bead",
        "coords": [420.0, 206.0, 552.0, 294.0],
        "file": "my_photo.jpg",
        "probability": 1.0,
    },
]

model_sample = [
    {
        "file": "demo_model.pt",
        "label": "YOLOv8 / all labels",
    },
]

models_sample = ["bin_model.onnx","multi_model.onnx"]

laser_output_sample = [
    {
        'binary_results': [
            {
                'file': 'frame_3204.png',
                'has_defect': True,
                'score': 0.5106827134975166,
                'probability': 0.5106827134975166
            },
             # ... (other binary results)
        ],
        'multi_results': {
            'indexes': [0, 10],
            'has_defect': True,
            'type': 'Irregular_Bead',
            'probability': 0.3904534578323364,
            'score': 0.3904534578323364
        }
    },
    # ... (other results)
]



class BinaryResultSchema(Schema):
    file = String()
    has_defect = Boolean()
    score = Float()
    probability = Float()

class MultiResultSchema(Schema):
    indexes = List(Integer())
    has_defect = Boolean()
    type = String()
    probability = Float()
    score = Float()

class LaserDefectsOut(Schema):
    binary_results = List(Nested(BinaryResultSchema))
    multi_results = Nested(MultiResultSchema)

class LaserDefectsFullOut(Schema):
    defect_models = List(String(), load_default=models_sample)
    results = List(Nested(LaserDefectsOut), load_default=laser_output_sample)
    inference_time = Float()
    mean_inference_time = Float()


class PhotoDefectsOut(Schema):
    type = String()
    coords = List(Integer(), many=True, validate=Length(4, 4))
    file = String()
    probability = Float()

class PhotoDefectsFullOut(Schema):
    defect_models = List(String(), load_default=models_sample)
    results = List(Nested(PhotoDefectsOut), load_default=damage_sample)
    inference_time = Float()
    mean_inference_time = Float()


class ModelsOut(Schema):
    file = String()
    label = String()


class ModelsFullOut(Schema):
    models = List(Nested(ModelsOut), load_default=model_sample)
