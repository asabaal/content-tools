from flask import render_template, request, jsonify
from . import views


def init_routes(app):
    @app.route('/')
    def index():
        data = views.get_transcript_data()
        return render_template('index.html', data=data)
    
    @app.route('/intent', methods=['POST'])
    def handle_intent():
        intent_data = request.get_json()
        intent_type = intent_data.get('intent_type')
        segment_id = intent_data.get('segment_id')
        take_id = intent_data.get('take_id')
        
        success = False
        if intent_type == 'select_segment':
            success = views.handle_select_segment(segment_id)
        elif intent_type == 'switch_take':
            success = views.handle_switch_take(take_id)
        
        if success:
            return jsonify({'status': 'success'}), 200
        else:
            return jsonify({'status': 'error'}), 400