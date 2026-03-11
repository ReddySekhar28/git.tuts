from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import json
import os

app = Flask(__name__)
app.secret_key = os.urandom(24) # Secret key for sessions

def get_db_connection():
    conn = sqlite3.connect('career.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- Authentication Routes ---

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()

    if user and check_password_hash(user['password'], password):
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        return jsonify({'success': True, 'message': 'Login successful'})
    else:
        return jsonify({'success': False, 'message': 'Invalid email or password'}), 401

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    education = data.get('education')

    if not all([name, email, password]):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400

    hashed_password = generate_password_hash(password)

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO users (name, email, password, education) VALUES (?, ?, ?, ?)',
            (name, email, hashed_password, education)
        )
        conn.commit()
        user_id = cursor.lastrowid
        session['user_id'] = user_id
        session['user_name'] = name
        success = True
        message = "Registration successful"
    except sqlite3.IntegrityError:
        success = False
        message = "Email already exists"
    finally:
        conn.close()

    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'message': message}), 409

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# --- Main App Routes ---

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # Fetch user's past evaluations
    conn = get_db_connection()
    evaluations = conn.execute(
        'SELECT * FROM evaluations WHERE user_id = ? ORDER BY created_at DESC', 
        (session['user_id'],)
    ).fetchall()
    conn.close()
    
    return render_template('dashboard.html', name=session['user_name'], evaluations=evaluations)

@app.route('/assessment')
def assessment():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('assessment.html')

# --- API Routes ---

@app.route('/api/metadata')
def get_metadata():
    conn = get_db_connection()
    roles = conn.execute('SELECT name, description FROM roles').fetchall()
    skills = conn.execute('SELECT name, category FROM skills').fetchall()
    conn.close()

    skill_dict = {}
    for skill in skills:
        cat = skill['category']
        if cat not in skill_dict:
            skill_dict[cat] = []
        skill_dict[cat].append(skill['name'])

    return jsonify({
        'roles': [dict(r) for r in roles],
        'skillsByCategory': skill_dict
    })

@app.route('/api/analyze', methods=['POST'])
def analyze():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.json
    selected_role = data.get('role')
    user_skills = data.get('skills', []) # List of dicts: [{'name': 'Python', 'proficiency': 'Advanced'}]
    user_projects = data.get('projects', [])

    conn = get_db_connection()
    role_record = conn.execute('SELECT * FROM roles WHERE name = ?', (selected_role,)).fetchone()

    if not role_record:
        conn.close()
        return jsonify({'error': 'Role not found'}), 404

    required_skills = json.loads(role_record['required_skills'])
    roadmap_data = json.loads(role_record['roadmap'])

    # Determine overlap using proficiencies
    weights = {"Beginner": 0.4, "Intermediate": 0.8, "Advanced": 1.0}
    user_skill_dict = {}
    
    for s in user_skills:
        if isinstance(s, dict):
            user_skill_dict[s['name'].lower()] = s.get('proficiency', 'Intermediate')
        else:
            user_skill_dict[str(s).lower()] = 'Intermediate'
            
    matched_skills = []
    missing_skills = []
    earned_score = 0.0

    for req in required_skills:
        req_lower = req.lower()
        if req_lower in user_skill_dict:
            prof = user_skill_dict[req_lower]
            earned_score += float(weights.get(prof, 0.5))
            matched_skills.append(f"{req} ({prof})")
        else:
            missing_skills.append(req)

    match_percentage = 0
    if len(required_skills) > 0:
        match_percentage = int((earned_score / float(len(required_skills))) * 100)
    
    # Bonus points for projects. Each project gives up to +5% if readiness < 100%
    if len(user_projects) > 0:
        match_percentage += min(len(user_projects) * 5, 100 - match_percentage)

    # Decorate roadmap with completion status
    for stage in roadmap_data:
        stage_skills = stage.get('skills_covered', [])
        if not stage_skills:
            stage['status'] = 'pending' 
        else:
            missing_in_stage = [s for s in stage_skills if s.lower() not in user_skill_dict]
            if len(missing_in_stage) == 0:
                stage['status'] = 'completed'
            elif len(missing_in_stage) < len(stage_skills):
                stage['status'] = 'in-progress'
            else:
                stage['status'] = 'pending'
                
    # Generate Mentor Feedback
    if match_percentage >= 80:
        strong_skills_list = [s.split(' ')[0] for i, s in enumerate(matched_skills) if i < 3]
        strong_skills = ', '.join(strong_skills_list) if matched_skills else "fundamentals"
        feedback = f"Outstanding profile! You have a strong command over {strong_skills}. You are highly ready for a {role_record['name']} role. Focus on polishing your portfolio projects and preparing for interviews."
    elif match_percentage >= 50:
        missing_focus_list = [s for i, s in enumerate(missing_skills) if i < 3]
        missing_focus = ', '.join(missing_focus_list) if missing_skills else "advanced topics"
        feedback = f"You are on the right track. You have a good foundation, but to hit the >80% readiness mark for a {role_record['name']}, you need to focus on learning {missing_focus}. Refer to the roadmap steps below."
    else:
        missing_focus_list = [s for i, s in enumerate(missing_skills) if i < 3]
        missing_focus = ', '.join(missing_focus_list) if missing_skills else "core technologies"
        feedback = f"You are at the beginning of your journey to become a {role_record['name']}. Don't worry, everyone starts here! Prioritize learning core skills like {missing_focus}. Follow Phase 1 of the roadmap closely."

    # Save evaluation
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO evaluations (user_id, role_name, readiness_score, matched_skills, missing_skills, roadmap, feedback)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        session['user_id'], 
        selected_role, 
        match_percentage, 
        json.dumps(matched_skills), 
        json.dumps(missing_skills), 
        json.dumps(roadmap_data),
        feedback
    ))
    conn.commit()
    conn.close()

    return jsonify({
        'role': role_record['name'],
        'description': role_record['description'],
        'readinessScore': match_percentage,
        'matchedSkills': matched_skills,
        'missingSkills': missing_skills,
        'roadmap': roadmap_data,
        'feedback': feedback
    })

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, port=5000)
