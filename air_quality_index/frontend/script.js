const apiUrl = `${window.location.protocol}//${window.location.host}`;

// State
let currentLat = 28.6139; // Default New Delhi
let currentLon = 77.2090;

// DOM Elements
const loginOverlay = document.getElementById('login-overlay');
const mainDashboard = document.getElementById('main-dashboard');
const userProfile = document.getElementById('user-profile');
const userImg = document.getElementById('user-img');
const userName = document.getElementById('user-name');
const devBypassBtn = document.getElementById('dev-bypass-btn');
const root = document.documentElement;

// Dashboard UI
const todayRing = document.getElementById('today-ring');
const todayValue = document.getElementById('today-value');
const todayStatus = document.getElementById('today-status');
const todayMsg = document.getElementById('today-msg');

const tomorrowRing = document.getElementById('tomorrow-ring');
const tomorrowValue = document.getElementById('tomorrow-value');
const tomorrowStatus = document.getElementById('tomorrow-status');
const tomorrowMsg = document.getElementById('tomorrow-msg');

const dayAfterRing = document.getElementById('day-after-ring');
const dayAfterValue = document.getElementById('day-after-value');
const dayAfterStatus = document.getElementById('day-after-status');
const dayAfterMsg = document.getElementById('day-after-msg');

const syncBtn = document.getElementById('live-sync-btn');

// Sliders mapping
const inputIds = ['PM2.5', 'PM10', 'CO', 'NO2', 'SO2', 'O3', 'Temperature', 'Humidity'];
const inputEls = {};
inputIds.forEach(id => {
    inputEls[id] = document.getElementById(id);
    if(inputEls[id]) {
        inputEls[id].addEventListener('input', (e) => {
            const displayId = `val-${id.toLowerCase().replace('.', '')}`;
            if(document.getElementById(displayId)) {
                document.getElementById(displayId).innerText = e.target.value;
            }
            debouncePredict();
        });
    }
});

let predictTimeout;
function debouncePredict() {
    clearTimeout(predictTimeout);
    predictTimeout = setTimeout(simulateTomorrow, 300);
}

// AQI Colors mapping
const aqiColors = {
    'Good': '#10b981', // var(--aqi-good)
    'Satisfactory': '#64dd17',
    'Moderate': '#f59e0b', // var(--aqi-moderate)
    'Poor': '#f97316', // var(--aqi-sensitive)
    'Very Poor': '#ef4444', // var(--aqi-unhealthy)
    'Severe / Hazardous': '#8b5cf6' // var(--aqi-very-unhealthy)
};

// =========================================================
// EMAIL LOGIN LOGIC
// =========================================================
const emailForm = document.getElementById('email-login-form');
const emailInput = document.getElementById('login-email');
const passInput = document.getElementById('login-password');
const loginError = document.getElementById('login-error');

if (emailForm) {
    emailForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        loginError.style.display = 'none';
        
        try {
            const res = await fetch(`${apiUrl}/login`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ email: emailInput.value, password: passInput.value })
            });
            const data = await res.json();
            
            if (data.success) {
                userProfile.style.display = 'flex';
                const safeName = encodeURIComponent(data.name || 'User');
                userImg.src = `https://ui-avatars.com/api/?name=${safeName}&background=random`;
                userName.innerText = data.name || 'User';
                
                loginOverlay.style.display = 'none';
                mainDashboard.style.display = 'flex';
                initDashboard();
            } else {
                loginError.innerText = data.error || "Login failed.";
                loginError.style.display = 'block';
            }
        } catch(err) {
            loginError.innerText = "Network Error ensuring connection.";
            loginError.style.display = 'block';
        }
    });
}

// =========================================================
// GOOGLE LOGIN (Legacy)
// =========================================================

function parseJwt(token) {
    var base64Url = token.split('.')[1];
    var base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    var jsonPayload = decodeURIComponent(window.atob(base64).split('').map(function(c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));
    return JSON.parse(jsonPayload);
}

window.handleCredentialResponse = (response) => {
    const data = parseJwt(response.credential);
    userProfile.style.display = 'flex';
    userImg.src = data.picture;
    userName.innerText = data.given_name || data.name;
    loginOverlay.style.display = 'none';
    mainDashboard.style.display = 'flex';
    initDashboard();
};

const guestLoginBtn = document.getElementById('guest-login-btn');
if (guestLoginBtn) {
    guestLoginBtn.addEventListener('click', () => {
        userProfile.style.display = 'flex';
        userImg.src = 'https://ui-avatars.com/api/?name=Guest+User&background=random';
        userName.innerText = 'Guest';
        loginOverlay.style.display = 'none';
        mainDashboard.style.display = 'flex';
        initDashboard();
    });
}

// =========================================================
// LOCATION & GEOCODING
// =========================================================

const gpsBtn = document.getElementById('gps-btn');
const searchCityInput = document.getElementById('city-search');
const searchBtn = document.getElementById('search-btn');
const locName = document.getElementById('location-name');

if (gpsBtn) {
    gpsBtn.addEventListener('click', () => {
        if (navigator.geolocation) {
            gpsBtn.style.color = 'var(--primary)'; // highlight
            navigator.geolocation.getCurrentPosition((position) => {
                currentLat = position.coords.latitude;
                currentLon = position.coords.longitude;
                locName.innerText = "My GPS Location";
                fetchLiveForecast();
                setTimeout(() => { gpsBtn.style.color = ''; }, 2000);
            }, (err) => {
                alert("Location access denied or failed.");
                gpsBtn.style.color = '';
            });
        } else {
            alert("Geolocation is not supported by this browser.");
        }
    });
}

async function searchCity() {
    const query = searchCityInput.value.trim();
    if (!query) return;
    
    // UI Loading state
    const originalIcon = searchBtn.innerHTML;
    searchBtn.innerHTML = '<div class="btn-loader"></div>';
    
    try {
        const res = await fetch(`https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(query)}&count=1`);
        const data = await res.json();
        
        if (data.results && data.results.length > 0) {
            const loc = data.results[0];
            currentLat = loc.latitude;
            currentLon = loc.longitude;
            locName.innerText = `${loc.name}, ${loc.country || ''}`;
            searchCityInput.value = ''; // clear
            fetchLiveForecast();
        } else {
            alert("City not found. Please try another name.");
        }
    } catch (e) {
        console.error("Geocoding Error:", e);
    } finally {
        searchBtn.innerHTML = originalIcon;
    }
}

if (searchBtn) {
    searchBtn.addEventListener('click', searchCity);
    searchCityInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            searchCity();
        }
    });
}

const quickCitySelect = document.getElementById('quick-city-select');
if (quickCitySelect) {
    quickCitySelect.addEventListener('change', (e) => {
        const city = e.target.value;
        if (city) {
            searchCityInput.value = city;
            searchCity();
        }
    });
}

const mapToggleBtn = document.getElementById('map-toggle-btn');
if (mapToggleBtn) {
    mapToggleBtn.addEventListener('click', () => {
        alert("Mini Map Feature coming soon! Searching for '" + locName.innerText + "' on local environmental maps.");
    });
}

// =========================================================
// BACKEND API & DATA FETCHING
// =========================================================

async function initDashboard() {
    initMap();
    await loadHistoricalData();
    await fetchLiveForecast();
}

let aqiMap, marker;
function initMap() {
    if (aqiMap) return;
    
    aqiMap = L.map('aqi-map', {
        center: [currentLat, currentLon],
        zoom: 5,
        zoomControl: false
    });

    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap &copy; CARTO'
    }).addTo(aqiMap);

    // Custom visible marker
    const markerIcon = L.divIcon({
        className: 'custom-div-icon',
        html: '<div class="marker-pin"></div><div class="marker-pulse"></div>',
        iconSize: [30, 42],
        iconAnchor: [15, 42]
    });
    marker = L.marker([currentLat, currentLon], { icon: markerIcon }).addTo(aqiMap);

    aqiMap.on('click', async (e) => {
        const { lat, lng } = e.latlng;
        currentLat = lat;
        currentLon = lng;
        marker.setLatLng([lat, lng]);
        
        // Try to get reverse geocode for a better header label
        locName.innerText = `Location: ${lat.toFixed(2)}, ${lng.toFixed(2)}`;
        await fetchLiveForecast();
    });
}

async function fetchLiveForecast() {
    const loader = syncBtn.querySelector('.btn-loader');
    const span = syncBtn.querySelector('span');
    
    loader.classList.remove('loader-hidden');
    span.innerText = "Syncing...";
    
    try {
        const response = await fetch(`${apiUrl}/live-forecast?lat=${currentLat}&lon=${currentLon}`);
        const data = await response.json();
        if(data.success) {
            updateDashboard(data.today, data.tomorrow, data.day_after_tomorrow);
            
            if (marker) marker.setLatLng([currentLat, currentLon]);
            if (aqiMap) aqiMap.setView([currentLat, currentLon], aqiMap.getZoom());
            
            const now = new Date();
            document.getElementById('live-timestamp').innerText = `Updated at ${now.getHours()}:${now.getMinutes().toString().padStart(2, '0')}`;
        }
    } catch (e) {
        console.error("Live Fetch Error:", e);
    } finally {
        loader.classList.add('loader-hidden');
        span.innerText = "Sync Live Data";
    }
}

syncBtn.addEventListener('click', fetchLiveForecast);

async function simulateTomorrow() {
    const payload = {};
    inputIds.forEach(id => {
        if(inputEls[id]) {
            payload[id] = parseFloat(inputEls[id].value);
        }
    });

    try {
        const response = await fetch(`${apiUrl}/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        
        if (data.success) {
            updateUI_Half('tomorrow', data.prediction);
        }
    } catch (error) {
        console.error("Prediction Error:", error);
    }
}

function updateDashboard(todayData, tomorrowData, dayAfterData) {
    updateUI_Half('today', todayData);
    updateUI_Half('tomorrow', tomorrowData);
    if (dayAfterData) updateUI_Half('day-after', dayAfterData);
    
    if(todayData.inputs) {
        const i = todayData.inputs;
        document.getElementById('live-pm25').innerText = i['PM2.5'].toFixed(1);
        document.getElementById('live-pm10').innerText = i['PM10'].toFixed(1);
        document.getElementById('live-no2').innerText = i['NO2'].toFixed(1);
        document.getElementById('live-o3').innerText = i['O3'].toFixed(1);
        
        Object.keys(todayData.inputs).forEach(key => {
            if(inputEls[key]) {
                inputEls[key].value = i[key];
                const displayId = `val-${key.toLowerCase().replace('.', '')}`;
                if(document.getElementById(displayId)) {
                    document.getElementById(displayId).innerText = Number(i[key]).toFixed(1);
                }
            }
        });
    }

    updateUI_Half('tomorrow', tomorrowData);
}

function updateUI_Half(side, prediction) {
    const aqi = prediction.aqi;
    const category = prediction.category;
    
    document.getElementById(`${side}-value`).innerText = Math.round(aqi);
    document.getElementById(`${side}-status`).innerText = category;
    document.getElementById(`${side}-msg`).innerText = prediction.recommendation;

    // --- New Health Insights ---
    const riskEl = document.getElementById(`${side}-risk`);
    const safetyEl = document.getElementById(`${side}-safety`);
    const asthmaEl = document.getElementById(`${side}-asthma`);
    const ringEl = document.getElementById(`${side}-ring`);

    if (riskEl) {
        riskEl.innerText = prediction.risk_level || 'Unknown Risk';
        riskEl.style.borderColor = prediction.color || 'rgba(255,255,255,0.2)';
    }

    if (safetyEl) {
        safetyEl.innerText = prediction.outdoor_safe ? '🍃 Safe Outdoors' : '🏠 Stay Indoors';
        if (prediction.outdoor_safe) {
            safetyEl.classList.remove('unsafe');
        } else {
            safetyEl.classList.add('unsafe');
        }
    }

    if (asthmaEl) {
        asthmaEl.innerText = prediction.asthma_alert || "";
        asthmaEl.style.display = prediction.asthma_alert ? "block" : "none";
    }

    // Apply Critical Animation if risk is High
    if (ringEl) {
        if (prediction.risk_code === 'high' || aqi > 200) {
            ringEl.classList.add('pulse-critical');
        } else {
            ringEl.classList.remove('pulse-critical');
        }
    }

    const color = prediction.color || aqiColors[category] || '#f8fafc';
    root.style.setProperty(`--${side}-color`, color);
}

// Chart.js Setup
let aqiChart;
async function loadHistoricalData() {
    try {
        const response = await fetch(`${apiUrl}/historical?days=5`);
        const data = await response.json();
        
        if (data.success) {
            const records = data.data;
            const labels = records.map(r => {
                const d = new Date(r.Date);
                return `${d.getMonth()+1}/${d.getDate()}`;
            });
            const aqiData = records.map(r => r.AQI);
            
            const ctx = document.getElementById('aqiChart').getContext('2d');
            if (aqiChart) aqiChart.destroy();
            
            aqiChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Historical AQI',
                        data: aqiData,
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        borderWidth: 2,
                        pointRadius: 2,
                        pointBackgroundColor: '#3b82f6',
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8', maxTicksLimit: 7 } },
                        y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } }
                    }
                }
            });
            
            // Build 5-Day Hazards timeline
            const hazardsContainer = document.getElementById('hazards-timeline');
            if (hazardsContainer && records.length > 0) {
                const total = records.length;
                const recToTake = Math.min(5, total);
                const recent5 = records.slice(total - recToTake).reverse();
                
                hazardsContainer.innerHTML = '';
                recent5.forEach(r => {
                    const dateObj = new Date(r.Date);
                    const formattedDate = dateObj.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
                    const color = aqiColors[r.Category] || '#f8fafc';
                    
                    const card = document.createElement('div');
                    card.className = 'hazard-card';
                    card.innerHTML = `
                        <div class="hc-indicator" style="background-color: ${color};"></div>
                        <div class="hc-date">${formattedDate}</div>
                        <div class="hc-aqi" style="color: ${color};">${Math.round(r.AQI)}</div>
                        <div class="hc-category" style="color: ${color};">${r.Category}</div>
                        <div class="hc-msg">${r.HazardMessage}</div>
                    `;
                    hazardsContainer.appendChild(card);
                });
            }
        }
    } catch (e) {
        console.error("Historical data error", e);
    }
}

// =========================================================
// AI CHAT & VOICE ASSISTANT
// =========================================================

let chatOpen = false;
let isListening = false;
let currentAqiContext = { aqi: 0, location: "your area" };

const aiChatBtn = document.getElementById('ai-chat-btn');
const aiChatBox = document.getElementById('ai-chat-box');
const closeChatBtn = document.getElementById('close-chat');
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const sendChatBtn = document.getElementById('send-chat');
const voiceBtn = document.getElementById('voice-btn');
const chatStatus = document.getElementById('chat-status');

// Toggle chat open/close
if (aiChatBtn) {
    aiChatBtn.addEventListener('click', () => {
        chatOpen = !chatOpen;
        aiChatBox.style.display = chatOpen ? 'flex' : 'none';
        if (chatOpen) {
            aiChatBox.style.flexDirection = 'column';
            chatInput.focus();
        }
    });
}

if (closeChatBtn) {
    closeChatBtn.addEventListener('click', () => {
        chatOpen = false;
        aiChatBox.style.display = 'none';
    });
}

// Send message logic
async function sendChatMessage(text) {
    if (!text.trim()) return;
    
    // Add user message bubble
    appendMessage(text, 'user');
    chatInput.value = '';
    
    // Show typing indicator
    const typingEl = appendMessage('...', 'ai typing');
    chatStatus.innerText = 'Thinking...';
    
    try {
        const res = await fetch(`${apiUrl}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                message: text, 
                context: currentAqiContext 
            })
        });
        const data = await res.json();
        
        // Remove typing indicator
        typingEl.remove();
        chatStatus.innerText = 'Online and ready';
        
        if (data.success) {
            const aiReply = data.response;
            appendMessage(aiReply, 'ai');
            speakText(aiReply);
        } else {
            appendMessage("Sorry, I couldn't process that. Please try again.", 'ai');
        }
    } catch (e) {
        typingEl.remove();
        chatStatus.innerText = 'Online and ready';
        appendMessage("Connection error. Please check if the server is running.", 'ai');
    }
}

function appendMessage(text, type) {
    const msg = document.createElement('div');
    msg.className = `message ${type === 'user' ? 'user-msg' : 'ai-msg'}`;
    msg.innerText = text;
    chatMessages.appendChild(msg);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return msg;
}

if (sendChatBtn) {
    sendChatBtn.addEventListener('click', () => sendChatMessage(chatInput.value));
}

if (chatInput) {
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendChatMessage(chatInput.value);
    });
}

// ── Voice Input (Speech Recognition) ──────────────────────────────────────────
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition;

if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
        isListening = true;
        voiceBtn.classList.add('active');
        chatStatus.innerText = 'Listening...';
        chatInput.placeholder = '🎤 Listening...';
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        chatInput.value = transcript;
        sendChatMessage(transcript);
    };

    recognition.onerror = () => {
        voiceBtn.classList.remove('active');
        chatStatus.innerText = 'Online and ready';
        chatInput.placeholder = 'Ask about AQI, health...';
        isListening = false;
    };

    recognition.onend = () => {
        voiceBtn.classList.remove('active');
        chatStatus.innerText = 'Online and ready';
        chatInput.placeholder = 'Ask about AQI, health...';
        isListening = false;
    };
}

if (voiceBtn) {
    voiceBtn.addEventListener('click', () => {
        if (!SpeechRecognition) {
            alert('Voice input is not supported in this browser. Please use Chrome or Edge.');
            return;
        }
        if (isListening) {
            recognition.stop();
        } else {
            recognition.start();
        }
    });
}

// ── Voice Output (Text-to-Speech) ─────────────────────────────────────────────
function speakText(text) {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel(); // Cancel any ongoing speech
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 0.9;
    // Prefer a natural voice if available
    const voices = window.speechSynthesis.getVoices();
    const preferred = voices.find(v => v.lang === 'en-US' && v.name.includes('Google')) || voices[0];
    if (preferred) utterance.voice = preferred;
    window.speechSynthesis.speak(utterance);
}

// ── Update AQI Context for Chat AI ───────────────────────────────────────────
// This function is called whenever the live forecast updates
function updateChatContext(location, aqi) {
    currentAqiContext = { location, aqi };
}
