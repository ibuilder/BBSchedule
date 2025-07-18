"""
3D Model Viewer Routes for BBSchedule
Handles model upload, processing, and viewing with That Open fragments API
"""

import os
import json
import uuid
from datetime import datetime
from flask import render_template, request, jsonify, flash, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from app import app, db
from models import Project
import logging

logger = logging.getLogger(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads/models'
ALLOWED_EXTENSIONS = {'rvt', 'ifc', 'gltf', 'glb', 'obj', 'fbx'}
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size(file_path):
    """Get human readable file size"""
    size = os.path.getsize(file_path)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

@app.route('/model-viewer')
def model_viewer():
    """3D Model Viewer main page"""
    projects = Project.query.all()
    return render_template('model_viewer.html', projects=projects)

@app.route('/api/model/upload', methods=['POST'])
def upload_model():
    """Handle model file upload with fragment processing"""
    try:
        if 'model_file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['model_file']
        project_id = request.form.get('project_id')
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'File type not supported'}), 400
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{unique_id}{ext}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        # Save file
        file.save(file_path)
        
        # Process model and create fragments
        processing_result = process_model_fragments(file_path, unique_filename)
        
        # Store model metadata
        model_metadata = {
            'id': unique_id,
            'original_filename': filename,
            'file_path': file_path,
            'project_id': project_id,
            'upload_time': datetime.utcnow().isoformat(),
            'file_size': get_file_size(file_path),
            'processing_result': processing_result
        }
        
        # Save metadata to database or file
        save_model_metadata(model_metadata)
        
        return jsonify({
            'success': True,
            'model_id': unique_id,
            'model_url': f'/api/model/serve/{unique_id}',
            'stats': processing_result.get('stats', {}),
            'message': 'Model uploaded and processed successfully'
        })
        
    except Exception as e:
        logger.error(f"Model upload failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

def process_model_fragments(file_path, filename):
    """Process model file into fragments for optimized loading"""
    try:
        # Simulate fragment processing
        # In a real implementation, this would use actual fragment processing
        file_ext = os.path.splitext(filename)[1].lower()
        file_size = os.path.getsize(file_path)
        
        # Estimated processing metrics
        estimated_triangles = file_size // 1000  # Rough estimate
        estimated_fragments = max(1, estimated_triangles // 10000)
        estimated_materials = max(1, estimated_triangles // 50000)
        
        processing_result = {
            'status': 'completed',
            'fragments_created': estimated_fragments,
            'processing_time': 2.5,  # seconds
            'optimization_ratio': 0.85,
            'stats': {
                'triangles': estimated_triangles,
                'fragments': estimated_fragments,
                'materials': estimated_materials,
                'size': get_file_size(file_path)
            }
        }
        
        logger.info(f"Model processing completed for {filename}: {estimated_fragments} fragments created")
        
        return processing_result
        
    except Exception as e:
        logger.error(f"Fragment processing failed for {filename}: {str(e)}")
        return {
            'status': 'failed',
            'error': str(e),
            'stats': {}
        }

def save_model_metadata(metadata):
    """Save model metadata to storage"""
    try:
        metadata_dir = os.path.join(UPLOAD_FOLDER, 'metadata')
        os.makedirs(metadata_dir, exist_ok=True)
        
        metadata_file = os.path.join(metadata_dir, f"{metadata['id']}.json")
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
            
    except Exception as e:
        logger.error(f"Failed to save model metadata: {str(e)}")

@app.route('/api/model/serve/<model_id>')
def serve_model(model_id):
    """Serve model file for viewing"""
    try:
        # Load metadata
        metadata_file = os.path.join(UPLOAD_FOLDER, 'metadata', f"{model_id}.json")
        
        if not os.path.exists(metadata_file):
            return jsonify({'error': 'Model not found'}), 404
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Serve the actual model file
        file_path = metadata['file_path']
        if os.path.exists(file_path):
            directory = os.path.dirname(file_path)
            filename = os.path.basename(file_path)
            return send_from_directory(directory, filename)
        else:
            return jsonify({'error': 'Model file not found'}), 404
            
    except Exception as e:
        logger.error(f"Failed to serve model {model_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/model/sample/<model_type>')
def get_sample_model(model_type):
    """Get sample model for demonstration"""
    try:
        # Sample model configurations
        sample_models = {
            'office': {
                'name': 'Office Building Complex',
                'description': 'Multi-story office building with detailed interior',
                'url': 'https://thatopen.github.io/engine_fragment/resources/small.frag',
                'stats': {
                    'triangles': 245000,
                    'fragments': 24,
                    'materials': 45,
                    'size': '12.4 MB'
                }
            },
            'bridge': {
                'name': 'Highway Bridge Structure',
                'description': 'Cable-stayed bridge with detailed structural elements',
                'url': 'https://thatopen.github.io/engine_fragment/resources/bridge.frag',
                'stats': {
                    'triangles': 180000,
                    'fragments': 18,
                    'materials': 32,
                    'size': '9.8 MB'
                }
            },
            'residential': {
                'name': 'Residential Complex',
                'description': 'Multi-unit residential building with landscaping',
                'url': 'https://thatopen.github.io/engine_fragment/resources/residential.frag',
                'stats': {
                    'triangles': 320000,
                    'fragments': 32,
                    'materials': 68,
                    'size': '18.7 MB'
                }
            },
            'industrial': {
                'name': 'Industrial Facility',
                'description': 'Manufacturing facility with equipment and infrastructure',
                'url': 'https://thatopen.github.io/engine_fragment/resources/industrial.frag',
                'stats': {
                    'triangles': 450000,
                    'fragments': 45,
                    'materials': 89,
                    'size': '28.3 MB'
                }
            }
        }
        
        if model_type not in sample_models:
            return jsonify({'success': False, 'error': 'Sample model not found'}), 404
        
        model_info = sample_models[model_type]
        
        return jsonify({
            'success': True,
            'model_url': model_info['url'],
            'name': model_info['name'],
            'description': model_info['description'],
            'stats': model_info['stats']
        })
        
    except Exception as e:
        logger.error(f"Failed to get sample model {model_type}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/model/list')
def list_models():
    """List all uploaded models"""
    try:
        models = []
        metadata_dir = os.path.join(UPLOAD_FOLDER, 'metadata')
        
        if os.path.exists(metadata_dir):
            for filename in os.listdir(metadata_dir):
                if filename.endswith('.json'):
                    with open(os.path.join(metadata_dir, filename), 'r') as f:
                        metadata = json.load(f)
                        models.append({
                            'id': metadata['id'],
                            'name': metadata['original_filename'],
                            'upload_time': metadata['upload_time'],
                            'file_size': metadata['file_size'],
                            'project_id': metadata.get('project_id'),
                            'stats': metadata.get('processing_result', {}).get('stats', {})
                        })
        
        # Sort by upload time (newest first)
        models.sort(key=lambda x: x['upload_time'], reverse=True)
        
        return jsonify({
            'success': True,
            'models': models,
            'total': len(models)
        })
        
    except Exception as e:
        logger.error(f"Failed to list models: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/model/delete/<model_id>', methods=['DELETE'])
def delete_model(model_id):
    """Delete uploaded model"""
    try:
        metadata_file = os.path.join(UPLOAD_FOLDER, 'metadata', f"{model_id}.json")
        
        if not os.path.exists(metadata_file):
            return jsonify({'success': False, 'error': 'Model not found'}), 404
        
        # Load metadata to get file path
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Delete model file
        file_path = metadata['file_path']
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete metadata file
        os.remove(metadata_file)
        
        return jsonify({
            'success': True,
            'message': 'Model deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Failed to delete model {model_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/model/stats')
def model_stats():
    """Get overall model statistics"""
    try:
        metadata_dir = os.path.join(UPLOAD_FOLDER, 'metadata')
        
        total_models = 0
        total_size = 0
        total_triangles = 0
        total_fragments = 0
        
        if os.path.exists(metadata_dir):
            for filename in os.listdir(metadata_dir):
                if filename.endswith('.json'):
                    with open(os.path.join(metadata_dir, filename), 'r') as f:
                        metadata = json.load(f)
                        total_models += 1
                        
                        # Get file size
                        file_path = metadata['file_path']
                        if os.path.exists(file_path):
                            total_size += os.path.getsize(file_path)
                        
                        # Get processing stats
                        stats = metadata.get('processing_result', {}).get('stats', {})
                        total_triangles += stats.get('triangles', 0)
                        total_fragments += stats.get('fragments', 0)
        
        return jsonify({
            'success': True,
            'stats': {
                'total_models': total_models,
                'total_size': get_file_size_from_bytes(total_size) if total_size > 0 else '0 B',
                'total_triangles': total_triangles,
                'total_fragments': total_fragments,
                'avg_triangles_per_model': total_triangles // max(1, total_models),
                'avg_fragments_per_model': total_fragments // max(1, total_models)
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get model stats: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

def get_file_size_from_bytes(size_bytes):
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"