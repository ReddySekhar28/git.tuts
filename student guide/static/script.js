document.addEventListener('DOMContentLoaded', () => {
    // Check if we are on the assessment page
    const appContainer = document.getElementById('app');
    if (!appContainer) return; // Not on assessment page

    // State
    let selectedRole = null;
    let userSkills = {}; // { "Python": "Intermediate" }
    let userProjects = [];

    // Elements
    const step1 = document.getElementById('step-1');
    const step2 = document.getElementById('step-2');
    const step3 = document.getElementById('step-3');
    const stepResults = document.getElementById('step-results');
    const progressBar = document.getElementById('progress-bar');

    const btnNext1 = document.getElementById('btn-next-1');
    const btnNext2 = document.getElementById('btn-next-2');
    const btnPrev2 = document.getElementById('btn-prev-2');
    const btnPrev3 = document.getElementById('btn-prev-3');
    const btnAnalyze = document.getElementById('btn-analyze');

    const addProjectBtn = document.getElementById('add-project-btn');
    const projectInput = document.getElementById('project-input');
    const projectsList = document.getElementById('projects-list');

    // Load Initial Data
    fetchMetadata();

    // Event Listeners
    if(btnNext1) btnNext1.addEventListener('click', () => { showStep(step2, step1); updateProgress(50); });
    if(btnNext2) btnNext2.addEventListener('click', () => { showStep(step3, step2); updateProgress(75); });
    if(btnPrev2) btnPrev2.addEventListener('click', () => { showStep(step1, step2); updateProgress(25); });
    if(btnPrev3) btnPrev3.addEventListener('click', () => { showStep(step2, step3); updateProgress(50); });
    if(btnAnalyze) btnAnalyze.addEventListener('click', performAnalysis);

    if(addProjectBtn) addProjectBtn.addEventListener('click', addProject);
    if(projectInput) {
        projectInput.addEventListener('keypress', (e) => {
            if(e.key === 'Enter') addProject();
        });
    }

    function updateProgress(percentage) {
        if(progressBar) progressBar.style.width = percentage + '%';
    }

    function showStep(showElement, hideElement) {
        hideElement.classList.add('hidden');
        hideElement.classList.remove('active');
        showElement.classList.remove('hidden');
        showElement.classList.add('active');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    async function fetchMetadata() {
        try {
            const res = await fetch('/api/metadata');
            if (res.status === 401) {
                window.location.href = '/'; // Redirect to login if unauthorized
                return;
            }
            if (!res.ok) throw new Error("Metadata fetch failed");
            const data = await res.json();
            renderRoles(data.roles);
            renderSkills(data.skillsByCategory);
        } catch (e) {
            console.error("Error loading metadata:", e);
            const container = document.getElementById('roles-container');
            if(container) container.innerHTML = '<p class="text-danger">Failed to load roles. Please ensure backend is running.</p>';
        }
    }

    function renderRoles(roles) {
        const container = document.getElementById('roles-container');
        if(!container) return;
        container.innerHTML = '';
        
        roles.forEach(role => {
            const card = document.createElement('div');
            card.className = 'role-card';
            card.innerHTML = `
                <h3>${role.name}</h3>
                <p>${role.description}</p>
            `;
            card.addEventListener('click', () => {
                document.querySelectorAll('.role-card').forEach(c => c.classList.remove('selected'));
                card.classList.add('selected');
                selectedRole = role.name;
                btnNext1.disabled = false;
            });
            container.appendChild(card);
        });
    }

    function renderSkills(skillsByCategory) {
        const container = document.getElementById('skills-container');
        if(!container) return;
        container.innerHTML = '';

        for (const [category, skills] of Object.entries(skillsByCategory)) {
            const group = document.createElement('div');
            group.className = 'skill-category';
            group.innerHTML = `<h3 style="margin-bottom: 0.8rem; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 0.5rem;">${category}</h3>`;
            
            const wrapper = document.createElement('div');
            wrapper.className = 'skills-wrapper';

            skills.forEach(skill => {
                const item = document.createElement('div');
                item.className = 'skill-item-container';
                
                const labelWrapper = document.createElement('div');
                labelWrapper.className = 'skill-label-wrapper';
                labelWrapper.innerHTML = `
                    <i class="far fa-circle check-icon"></i>
                    <span>${skill}</span>
                `;

                const select = document.createElement('select');
                select.className = 'proficiency-select';
                select.innerHTML = `
                    <option value="Beginner">Beginner</option>
                    <option value="Intermediate">Intermediate</option>
                    <option value="Advanced">Advanced</option>
                `;

                labelWrapper.addEventListener('click', () => {
                    const icon = labelWrapper.querySelector('.check-icon');
                    if (skill in userSkills) {
                        delete userSkills[skill];
                        item.classList.remove('selected');
                        icon.classList.replace('fa-check-circle', 'fa-circle');
                        icon.classList.replace('fas', 'far');
                    } else {
                        userSkills[skill] = select.value;
                        item.classList.add('selected');
                        icon.classList.replace('fa-circle', 'fa-check-circle');
                        icon.classList.replace('far', 'fas');
                    }
                });

                select.addEventListener('change', (e) => {
                    if (skill in userSkills) {
                        userSkills[skill] = e.target.value;
                    }
                });

                item.appendChild(labelWrapper);
                item.appendChild(select);
                wrapper.appendChild(item);
            });

            group.appendChild(wrapper);
            container.appendChild(group);
        }
    }

    function addProject() {
        if(!projectInput) return;
        const val = projectInput.value.trim();
        if (val) {
            userProjects.push(val);
            const li = document.createElement('li');
            li.innerHTML = `<span>${val}</span> <button aria-label="Remove project"><i class="fas fa-times"></i></button>`;
            li.querySelector('button').addEventListener('click', () => {
                userProjects = userProjects.filter(p => p !== val);
                li.remove();
            });
            projectsList.appendChild(li);
            projectInput.value = '';
        }
    }

    async function performAnalysis() {
        const originalText = btnAnalyze.innerHTML;
        btnAnalyze.innerHTML = '<div class="loading-spinner" style="width:20px;height:20px;border-width:2px;margin:0;"></div> <span style="margin-left:8px;">Analyzing...</span>';
        btnAnalyze.disabled = true;

        try {
            // Convert dictionary to array of objects for easier backend processing later
            const formattedSkills = Object.entries(userSkills).map(([name, prof]) => ({
                name: name,
                proficiency: prof
            }));

            const payload = {
                role: selectedRole,
                skills: formattedSkills,
                projects: userProjects
            };

            const res = await fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            if (res.status === 401) {
                window.location.href = '/';
                return;
            }
            
            const data = await res.json();

            renderResults(data);
            showStep(stepResults, step3);
            updateProgress(100);
        } catch (e) {
            console.error("Analysis error", e);
            alert("Error analyzing profile. Make sure you are logged in.");
        } finally {
            btnAnalyze.innerHTML = originalText;
            btnAnalyze.disabled = false;
        }
    }

    function renderResults(data) {
        document.getElementById('result-role').textContent = data.role;
        document.getElementById('result-desc').textContent = data.description;
        
        const feedbackEl = document.getElementById('mentor-feedback');
        if (feedbackEl && data.feedback) {
            feedbackEl.textContent = data.feedback;
        }

        // Animate circular progress
        const circle = document.getElementById('score-circle');
        const scoreText = document.getElementById('score-text');
        let currentScore = 0;
        const targetScore = data.readinessScore;
        
        const animate = setInterval(() => {
            if(currentScore >= targetScore) {
                clearInterval(animate);
                scoreText.textContent = targetScore + '%';
                circle.style.background = `conic-gradient(var(--accent) ${targetScore * 3.6}deg, rgba(255,255,255,0.1) 0deg)`;
            } else {
                currentScore++;
                scoreText.textContent = currentScore + '%';
                circle.style.background = `conic-gradient(var(--accent) ${currentScore * 3.6}deg, rgba(255,255,255,0.1) 0deg)`;
            }
        }, 15);

        if(targetScore === 0) {
            scoreText.textContent = '0%';
            circle.style.background = `conic-gradient(var(--accent) 0deg, rgba(255,255,255,0.1) 0deg)`;
        }

        // Skills Match / Miss
        const matchedList = document.getElementById('matched-skills-list');
        const missingList = document.getElementById('missing-skills-list');
        
        matchedList.innerHTML = data.matchedSkills.length ? 
            data.matchedSkills.map(s => `<li>${s}</li>`).join('') : '<li>None</li>';
            
        missingList.innerHTML = data.missingSkills.length ? 
            data.missingSkills.map(s => `<li>${s}</li>`).join('') : '<li style="color:var(--success);">None! You have everything you need!</li>';

        // Roadmap
        const timeline = document.getElementById('roadmap-timeline');
        timeline.innerHTML = '';

        data.roadmap.forEach((stage, idx) => {
            let statusText = 'Pending';
            let statusClass = 'status-pending';
            
            if (stage.status === 'completed') {
                statusText = 'Completed';
                statusClass = 'status-completed';
            } else if (stage.status === 'in-progress') {
                statusText = 'In Progress';
                statusClass = 'status-in-progress';
            }

            const item = document.createElement('div');
            item.className = `timeline-item ${stage.status}`;
            item.innerHTML = `
                <div class="timeline-marker"></div>
                <div class="timeline-content">
                    <h4>Stage ${stage.stage}: ${stage.title}</h4>
                    <span class="timeline-status ${statusClass}">${statusText}</span>
                    <p>${stage.desc}</p>
                    ${stage.skills_covered && stage.skills_covered.length > 0 ? 
                        `<p style="margin-top: 10px; font-size: 0.85rem; color: #58a6ff;">
                            <strong>Skills target:</strong> ${stage.skills_covered.join(', ')}
                        </p>` : ''
                    }
                </div>
            `;
            timeline.appendChild(item);
        });
    }
});
