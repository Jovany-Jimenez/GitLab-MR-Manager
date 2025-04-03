#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import argparse
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import gitlab
import logging

# Remove the circular import
# from create_gitlab_mrs import detect_default_branch, get_gitlab_project_id

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Global variables to store project data
PROJECTS_DATA = []
TARGET_DIR = ""
GITLAB_TOKEN = ""
BRANCH_NAME = ""
COMMIT_MESSAGE = ""
MR_TITLE = ""
MR_DESCRIPTION = ""

# Store the original working directory
ORIGINAL_WORKING_DIR = os.getcwd()

# Add the functions that were previously imported
def detect_default_branch(project_dir):
    """Detect the default branch of a Git repository"""
    try:
        # Try to get the default branch from the repository
        os.chdir(project_dir)
        
        # First check if main exists
        result = subprocess.run(
            ["git", "show-ref", "--verify", "--quiet", "refs/heads/main"],
            capture_output=True
        )
        if result.returncode == 0:
            return "main"
        
        # Then check if master exists
        result = subprocess.run(
            ["git", "show-ref", "--verify", "--quiet", "refs/heads/master"],
            capture_output=True
        )
        if result.returncode == 0:
            return "master"
        
        # If neither main nor master, try to get the current branch
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        
        # If all else fails, return None
        return None
    except Exception as e:
        print(f"Error detecting default branch: {e}")
        return None

def get_gitlab_project_id(project_dir):
    """Get the GitLab project ID for a Git repository"""
    try:
        os.chdir(project_dir)
        
        # Get the remote URL
        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            print(f"Error getting remote URL: {result.stderr}")
            return None
        
        remote_url = result.stdout.strip()
        
        # Extract project path from URL (handles various formats)
        if remote_url.startswith("git@"):
            # Format: git@gitlab.com:namespace/project.git
            path = remote_url.split(':', 1)[1]
        elif remote_url.startswith("https://"):
            # Format: https://gitlab.com/namespace/project.git
            path = remote_url.split('/', 3)[3]
        else:
            print(f"Unrecognized remote URL format: {remote_url}")
            return None
        
        # Remove .git suffix if present
        if path.endswith(".git"):
            path = path[:-4]
            
        return path
    except Exception as e:
        print(f"Error getting GitLab project ID: {e}")
        return None

def scan_projects(directory):
    """Scan directory for git projects with modified files"""
    projects = []
    
    # Always restore the working directory after the function exits
    original_dir = os.getcwd()
    
    try:
        for item in os.listdir(directory):
            project_dir = os.path.join(directory, item)
            if os.path.isdir(project_dir) and os.path.isdir(os.path.join(project_dir, '.git')):
                try:
                    os.chdir(project_dir)
                    
                    # Get diff for all changes in the repository
                    result = subprocess.run(
                        ["git", "diff", "--unified=10", "--no-color"],
                        capture_output=True, text=True
                    )
                    
                    if result.stdout.strip():
                        # Format the diff for display in Diff2Html:
                        clean_diff = f"diff --git a/ b/\n{result.stdout}"
                        
                        # Get default branch
                        target_branch = detect_default_branch(project_dir)
                        
                        projects.append({
                            "name": item,
                            "path": project_dir,
                            "diff": clean_diff,
                            "target_branch": target_branch,
                            "selected": True  # Default to selected
                        })
                        
                    # Restore working directory after each operation
                    os.chdir(original_dir)
                except Exception as e:
                    print(f"Error scanning project {item}: {e}")
                    # Always restore directory if an error occurs
                    os.chdir(original_dir)
    except Exception as e:
        print(f"Error scanning directory: {e}")
    finally:
        # Always restore the original directory
        os.chdir(original_dir)
                    
    return projects

def create_mr_for_project(project, branch_name, commit_message, mr_title, mr_description, gitlab_token):
    """Create a merge request for a single project"""
    try:
        os.chdir(project["path"])
        project_name = os.path.basename(project["path"])
        
        # Get the current branch to return to it later
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True
        )
        current_branch = result.stdout.strip() if result.returncode == 0 else "main"
            
        # Create and checkout new branch
        result = subprocess.run(
            ["git", "checkout", "-b", branch_name], 
            capture_output=True, text=True
        )
        if result.returncode != 0:
            # Branch might already exist, try checking it out
            result = subprocess.run(
                ["git", "checkout", branch_name],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                return False, f"Failed to create/checkout branch: {result.stderr}"
            
        # Add modified file
        result = subprocess.run(
            ["git", "add", ".gitlab-ci.yml"], 
            capture_output=True, text=True
        )
        if result.returncode != 0:
            subprocess.run(["git", "checkout", current_branch], capture_output=True)
            return False, f"Failed to stage changes: {result.stderr}"
            
        # Commit changes
        result = subprocess.run(
            ["git", "commit", "-m", commit_message], 
            capture_output=True, text=True
        )
        if result.returncode != 0:
            subprocess.run(["git", "checkout", current_branch], capture_output=True)
            return False, f"Failed to commit changes: {result.stderr}"
            
        # Push branch
        result = subprocess.run(
            ["git", "push", "-u", "origin", branch_name],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            subprocess.run(["git", "checkout", current_branch], capture_output=True)
            return False, f"Failed to push branch: {result.stderr}"
        
        # Create merge request on GitLab
        if project["target_branch"] and gitlab_token:
            try:
                project_path = get_gitlab_project_id(project["path"])
                if not project_path:
                    return False, "Could not determine GitLab project path"
                
                gl = gitlab.Gitlab('https://gitlab.com', private_token=gitlab_token)
                gl_project = gl.projects.get(project_path)
                
                mr = gl_project.mergerequests.create({
                    'source_branch': branch_name,
                    'target_branch': project["target_branch"],
                    'title': mr_title,
                    'description': mr_description,
                    'remove_source_branch': True,
                })
                
                subprocess.run(["git", "checkout", current_branch], capture_output=True)
                return True, f"Created MR: {mr.web_url}"
            except Exception as e:
                return False, f"Failed to create MR: {str(e)}"
        
        subprocess.run(["git", "checkout", current_branch], capture_output=True)
        return True, f"Created branch {branch_name} but no MR created"
        
    except Exception as e:
        return False, f"Exception: {str(e)}"

# Flask routes
@app.route('/')
def index():
    return render_template('index.html', projects=PROJECTS_DATA)

@app.route('/scan', methods=['POST'])
def scan():
    global PROJECTS_DATA, TARGET_DIR
    TARGET_DIR = request.form.get('target_dir', '')
    
    if not TARGET_DIR or not os.path.isdir(TARGET_DIR):
        flash('Please provide a valid directory path', 'error')
        return redirect(url_for('index'))
        
    PROJECTS_DATA = scan_projects(TARGET_DIR)
    
    if not PROJECTS_DATA:
        flash('No projects with modifications found', 'warning')
    
    return redirect(url_for('index'))

@app.route('/project/<int:project_id>')
def view_project(project_id):
    try:
        project_id = int(project_id)
        print(f"Debug: Accessing project_id {project_id}")
        
        if 0 <= project_id < len(PROJECTS_DATA):
            print(f"Debug: Project found: {PROJECTS_DATA[project_id]['name']}")
            print(f"Debug: Rendering project_details.html with data: {PROJECTS_DATA[project_id]['name']}")
            return render_template('project_details.html', 
                                  project=PROJECTS_DATA[project_id], 
                                  project_id=project_id)
        else:
            print(f"Debug: Project ID {project_id} out of range. Available projects: {len(PROJECTS_DATA)}")
            print(f"Debug: Project IDs available: {[i for i in range(len(PROJECTS_DATA))]}")
            flash('Project not found', 'error')
            return redirect(url_for('index'))
    except Exception as e:
        print(f"Error in view_project: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f'Error viewing project: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/update_selection', methods=['POST'])
def update_selection():
    data = request.json
    project_id = data.get('project_id')
    selected = data.get('selected')
    
    if 0 <= project_id < len(PROJECTS_DATA):
        PROJECTS_DATA[project_id]['selected'] = selected
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Project not found'})

@app.route('/create_mrs', methods=['POST'])
def create_mrs():
    global BRANCH_NAME, COMMIT_MESSAGE, MR_TITLE, MR_DESCRIPTION, GITLAB_TOKEN
    
    BRANCH_NAME = request.form.get('branch_name', 'add-change-management')
    COMMIT_MESSAGE = request.form.get('commit_message', 'Add Change Management integration')
    MR_TITLE = request.form.get('mr_title', 'Add Change Management integration')
    MR_DESCRIPTION = request.form.get('mr_description', 'Adding Change Management integration to CI pipeline')
    GITLAB_TOKEN = request.form.get('gitlab_token', os.environ.get('GITLAB_API_TOKEN', ''))
    
    if not GITLAB_TOKEN:
        flash('GitLab token is required to create merge requests', 'error')
        return redirect(url_for('index'))
    
    selected_projects = [p for p in PROJECTS_DATA if p.get('selected', False)]
    
    if not selected_projects:
        flash('No projects selected', 'warning')
        return redirect(url_for('index'))
    
    results = []
    for project in selected_projects:
        success, message = create_mr_for_project(
            project, 
            BRANCH_NAME,
            COMMIT_MESSAGE,
            MR_TITLE,
            MR_DESCRIPTION,
            GITLAB_TOKEN
        )
        
        results.append({
            'project': project['name'],
            'success': success,
            'message': message
        })
    
    with open('mr_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    return render_template('results.html', results=results)

@app.route('/debug')
def debug_info():
    """Route to show debug information"""
    template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    
    return jsonify({
        'working_directory': os.getcwd(),
        'original_directory': ORIGINAL_WORKING_DIR,
        'template_dir_exists': os.path.exists(template_dir),
        'static_dir_exists': os.path.exists(static_dir),
        'projects_count': len(PROJECTS_DATA),
        'templates': os.listdir(template_dir) if os.path.exists(template_dir) else [],
        'static_files': os.listdir(static_dir) if os.path.exists(static_dir) else []
    })

@app.route('/static/js/debug.js')
def debug_js():
    """Serve debug JavaScript"""
    return """
console.log('Debug script loaded');
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded');
    
    // Log all projects
    const projects = JSON.parse(document.getElementById('projects-data').textContent);
    console.log('Projects:', projects);
    
    // Add click handlers to view changes buttons
    document.querySelectorAll('.view-changes-btn').forEach(function(btn) {
        console.log('Found view changes button for project:', btn.getAttribute('data-id'));
        btn.addEventListener('click', function(e) {
            console.log('View changes clicked for project:', this.getAttribute('data-id'));
        });
    });
});
""", {'Content-Type': 'application/javascript'}

@app.route('/file-content')
def file_content():
    """Return the content of a file"""
    project_path = request.args.get('project_path')
    file_name = request.args.get('file', '.gitlab-ci.yml')
    
    if not project_path:
        return "No project path provided", 400
    
    file_path = os.path.join(project_path, file_name)
    
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        return f"File not found: {file_path}", 404
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}", 500

@app.route('/test-project/<int:project_id>')
def test_project(project_id):
    """A simple test route to check if project access works"""
    try:
        if 0 <= project_id < len(PROJECTS_DATA):
            return jsonify({
                'success': True,
                'project_name': PROJECTS_DATA[project_id]['name'],
                'project_path': PROJECTS_DATA[project_id]['path']
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Project ID {project_id} not found',
                'total_projects': len(PROJECTS_DATA)
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

def main():
    parser = argparse.ArgumentParser(description="Web Interface for GitLab MR Creation")
    parser.add_argument("--port", type=int, default=5001, help="Port to run the web server on")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    parser.add_argument("--target-dir", help="Optional: pre-fill target directory and scan on startup")
    
    args = parser.parse_args()
    
    print(f"Starting web server on http://localhost:{args.port}")
    print("Press Ctrl+C to stop the server")
    
    # Pre-scan projects if a target directory is provided
    if args.target_dir and os.path.isdir(args.target_dir):
        global TARGET_DIR, PROJECTS_DATA
        TARGET_DIR = args.target_dir
        # Store current directory
        current_dir = os.getcwd()
        PROJECTS_DATA = scan_projects(TARGET_DIR)
        # Restore to the original directory
        os.chdir(ORIGINAL_WORKING_DIR)
        print(f"Pre-scanned {len(PROJECTS_DATA)} projects in {TARGET_DIR}")
    
    # Enable more verbose logging
    if args.debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger('werkzeug')
        logger.setLevel(logging.DEBUG)
        # Log the current working directory
        print(f"Current working directory: {os.getcwd()}")
        print(f"Original working directory: {ORIGINAL_WORKING_DIR}")
        print(f"__file__: {__file__}")
        print(f"Absolute path: {os.path.abspath(__file__)}")
    
    # Use an application factory pattern to fix reloading issues
    os.environ['FLASK_APP'] = os.path.abspath(__file__)
    
    app.run(host="0.0.0.0", port=args.port, debug=args.debug)

if __name__ == "__main__":
    main()
