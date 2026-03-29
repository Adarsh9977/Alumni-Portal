const API = window.location.origin, token = localStorage.getItem('token'), user = JSON.parse(localStorage.getItem('user') || 'null');
if (!token || !user) { if (!['/login', '/register', '/'].includes(window.location.pathname)) location.href = '/login'; }

function H() { return { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` }; }
function toast(m) { const c = document.getElementById('toastContainer'); const d = document.createElement('div'); d.className = 'ln-toast'; d.textContent = m; c.appendChild(d); setTimeout(() => d.remove(), 3000); }

window.showTab = function(name) {
    document.querySelectorAll('.jec-tab').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.ln-tab-content').forEach(c => c.classList.remove('active'));
    const cap = name.charAt(0).toUpperCase() + name.slice(1);
    const t = document.getElementById(`tab${cap}`), c = document.getElementById(`content${cap}`);
    if (t) t.classList.add('active'); if (c) c.classList.add('active');
    if (name === 'feed') loadPosts(); if (name === 'directory') loadDirectory(); if (name === 'applications') loadMyApps();
};

function avatarColor(n) { const co = ['#800000','#d4af37','#057642','#1a1a1a','#600000']; let h = 0; for (let i = 0; i < n.length; i++) h = n.charCodeAt(i) + ((h << 5) - h); return co[Math.abs(h) % co.length]; }
function timeAgo(d) { if (!d) return ''; const s = Math.floor((Date.now() - new Date(d)) / 1000); if (s < 60) return 'now'; if (s < 3600) return `${Math.floor(s / 60)}m`; if (s < 86400) return `${Math.floor(s / 3600)}h`; return `${Math.floor(s / 86400)}d`; }

function init() {
    if (!user) return;
    const ini = user.name.charAt(0).toUpperCase();
    const els = { 'navUserName': user.name, 'navUserRole': user.role, 'navAvatar': ini, 'sideAvatar': ini, 'sideName': user.name, 'sideRole': user.role, 'sideBatch': user.batch || '—', 'sideHeadline': user.bio || (user.branch ? `${user.branch} · ${user.role}` : user.role), 'profileName': user.name || '', 'profileBatch': user.batch || '', 'profileBranch': user.branch || '', 'profileCompany': user.company || '', 'profileBio': user.bio || '', 'postAvatar': ini };
    Object.entries(els).forEach(([id, val]) => { const el = document.getElementById(id); if (el) { if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') el.value = val; else el.textContent = val; } });
    
    loadConnectionCount();
    
    // Update Profile Pictures across UI
    const upic = user.profile_picture;
    ['navAvatar', 'sideAvatar', 'postAvatar', 'profileAvatarPreview'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            if (upic) {
                el.innerHTML = `<img src="${upic}" style="width:100%; height:100%; border-radius:50%; object-fit:cover;">`;
                el.style.background = 'none';
            } else {
                el.textContent = ini;
                el.style.background = avatarColor(user.name);
            }
        }
    });
    
    if (user.ats_score) { 
        const b = document.getElementById('atsScoreBadge'), v = document.getElementById('atsScoreValue'), f = document.getElementById('atsFeedback'), p = document.getElementById('resumePrompt'), a = document.getElementById('resumeAnalysis');
        if (b) b.style.display = 'block'; if (v) v.textContent = user.ats_score; if (f) f.innerHTML = user.ats_feedback || 'Audit Complete.'; if (p) p.style.display = 'none'; if (a) a.style.display = 'block';
    }
    ['tabApplications', 'tabAdmin'].forEach(t => { const el = document.getElementById(t); if (el) el.style.display = (t === 'tabAdmin' ? user.role === 'admin' : user.role === 'student') ? 'block' : 'none'; });
    
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) logoutBtn.onclick = (e) => { e.preventDefault(); localStorage.clear(); location.href = '/login'; };
    
    loadPosts(); loadPendingConnectionRequests();
}

window.loadPosts = async function() {
    try {
        const r = await fetch(`${API}/api/posts/`, { headers: H() });
        const ps = await r.json();
        const c = document.getElementById('postsContainer'); if (!c) return;
        if (!ps.length) { c.innerHTML = '<div class="jec-card" style="padding:40px; text-align:center; color:#888;">No conversations yet. Start one!</div>'; return; }
        c.innerHTML = ps.map(p => `
            <div class="jec-post">
                <div class="ln-post-header">
                    <div class="ln-post-avatar" style="background:${p.author_pic ? 'none' : avatarColor(p.author_name)}">
                        ${p.author_pic ? `<img src="${p.author_pic}" style="width:100%; height:100%; border-radius:50%; object-fit:cover;">` : p.author_name.charAt(0).toUpperCase()}
                    </div>
                    <div class="ln-post-info">
                        <div class="ln-post-name"><a href="#">${p.author_name}</a> <span class="ln-post-role">${p.author_role}</span></div>
                        <div class="ln-post-meta">${timeAgo(p.created_at)}</div>
                    </div>
                </div>
                <div class="ln-post-body">${p.title ? `<strong style="display:block;margin-bottom:8px;font-size:1.1rem;color:var(--jec-maroon);">${p.title}</strong>` : ''}${p.content}</div>
                <div class="ln-post-actions">
                    <button class="ln-post-action" onclick="toggleLike(${p.id})"><i class="fas fa-thumbs-up"></i> ${p.like_count || ''} Like</button>
                    <button class="ln-post-action" onclick="toast('Comments optimized correctly.')"><i class="fas fa-comment"></i> ${p.comment_count || ''} Comment</button>
                    ${(p.author_id === user.id || user.role === 'admin') ? `<button class="ln-post-action" style="color:var(--jec-maroon);" onclick="deletePost(${p.id})"><i class="fas fa-trash"></i></button>` : ''}
                </div>
            </div>
        `).join('');
    } catch (e) { toast('Failed to load community feed.'); }
};

window.loadDirectory = async function() {
    const s = document.getElementById('searchName').value, b = document.getElementById('searchBatch').value, c = document.getElementById('searchCompany').value;
    let url = `${API}/api/users/directory?`;
    if (s) url += `search=${encodeURIComponent(s)}&`; if (b) url += `batch=${encodeURIComponent(b)}&`; if (c) url += `company=${encodeURIComponent(c)}&`;
    const container = document.getElementById('directoryContainer');
    container.innerHTML = '<div class="jec-loading-state"><i class="fas fa-spinner fa-spin"></i> Searching Registry...</div>';
    try {
        const r = await fetch(url, { headers: H() });
        const al = await r.json();
        
        // Clear search inputs after fetch
        document.getElementById('searchName').value = '';
        document.getElementById('searchBatch').value = '';
        document.getElementById('searchCompany').value = '';
        
        if (!al.length) { container.innerHTML = '<div class="jec-loading-state">No matching alumni found.</div>'; return; }
        container.innerHTML = al.map(a => `
            <div class="ln-member">
                <div class="ln-member-avatar" style="background:${a.profile_picture ? 'none' : avatarColor(a.name)}">
                    ${a.profile_picture ? `<img src="${a.profile_picture}" style="width:100%; height:100%; border-radius:50%; object-fit:cover;">` : a.name.charAt(0).toUpperCase()}
                </div>
                <div class="ln-member-info" style="cursor:pointer;" onclick="viewProfile('${a.name.replace(/'/g,"\\'")}', '${a.role}', '${a.company||"JEC Alumni"}', '${a.branch||"Engineer"}', '${(a.bio||"Dedicated member of the JEC community.").replace(/'/g,"\\'").replace(/\n/g," ")}', '${(a.skills||"All-rounder").replace(/'/g,"\\'")}', '${a.profile_picture || ""}')">
                    <div class="ln-member-name">${a.name}</div>
                    <div class="ln-member-detail">${a.company || 'JEC Alumni'} · ${a.branch || '—'} · Batch ${a.batch || '—'}</div>
                </div>
                <div style="display:flex; gap:8px;">
                    <button class="jec-btn-primary jec-btn-sm" onclick="sendConnection(${a.id}, this)">Connect</button>
                </div>
            </div>
        `).join('');
    } catch (e) { toast('Search Engine offline.'); }
};

window.viewProfile = function(name, role, company, branch, bio, skills, pic) {
    document.getElementById('pModalName').textContent = name;
    document.getElementById('pModalRole').textContent = role;
    document.getElementById('pModalHeadline').textContent = branch;
    document.getElementById('pModalCompany').textContent = company;
    document.getElementById('pModalBio').textContent = bio;
    document.getElementById('pModalSkills').textContent = skills;
    const av = document.getElementById('pModalAvatar');
    if (pic) {
        av.innerHTML = `<img src="${pic}" style="width:100%; height:100%; border-radius:50%; object-fit:cover;">`;
        av.style.background = 'none';
    } else {
        av.textContent = name.charAt(0).toUpperCase();
        av.style.background = avatarColor(name);
    }
    document.getElementById('profileModal').classList.add('active');
};

window.sendConnection = async function(id, btn) {
    btn.disabled = true; btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Pending';
    try { const r = await fetch(`${API}/api/connections/`, { method: 'POST', headers: H(), body: JSON.stringify({ receiver_id: id }) }); if (r.ok) toast('Connection request sent!'); } catch (e) { toast('Action failed.'); }
};

window.loadPendingConnectionRequests = async function() {
    try {
        const r = await fetch(`${API}/api/connections/pending`, { headers: H() });
        const rs = await r.json();
        const c = document.getElementById('requestsContainer'); if (!c) return;
        if (!rs.length) { c.innerHTML = '<p style="font-size:0.75rem; color:#888; text-align:center; padding:10px;">No pending invites.</p>'; return; }
        c.innerHTML = rs.map(req => `
            <div style="display:flex; justify-content:space-between; align-items:center; padding-top:10px;">
                <div style="font-size:0.8rem; font-weight:700;">${req.sender_name}</div>
                <div style="display:flex; gap:5px;">
                    <button class="jec-btn-primary jec-btn-sm" style="padding:4px 8px; border-radius:4px;" onclick="respondReq(${req.id},'accepted')"><i class="fas fa-check"></i></button>
                    <button class="jec-btn-primary jec-btn-sm" style="background:#eee; color:#666; padding:4px 8px; border-radius:4px;" onclick="respondReq(${req.id},'rejected')"><i class="fas fa-times"></i></button>
                </div>
            </div>
        `).join('');
    } catch (e) { }
};

window.respondReq = async function(id, status) {
    try {
        const r = await fetch(`${API}/api/connections/${id}/status`, { method: 'PUT', headers: H(), body: JSON.stringify({ status }) });
        if (r.ok) { toast(`Professional request ${status}.`); loadPendingConnectionRequests(); loadConnectionCount(); }
    } catch (e) { toast('Error synchronizing invitation.'); }
};

window.loadConnectionCount = async function() {
    try {
        const r = await fetch(`${API}/api/connections/count`, { headers: H() });
        const d = await r.json();
        const el = document.getElementById('sideConnections');
        if (el) el.textContent = d.count || '0';
    } catch (e) { }
};

window.uploadResume = async function() {
    const f = document.getElementById('resumeFile'); if (!f || !f.files[0]) return;
    const formData = new FormData(); formData.append('file', f.files[0]);
    const btn = document.querySelector('.jec-btn-outline'); btn.disabled = true; btn.innerHTML = '<i class="fas fa-microchip fa-spin"></i> Analyzing...';
    try {
        const r = await fetch(`${API}/api/resume/upload`, { method: 'POST', headers: { 'Authorization': `Bearer ${token}` }, body: formData });
        const d = await r.json();
        if (r.ok) { toast('AI Audit Complete!'); user.ats_score = d.score; user.ats_feedback = d.feedback; localStorage.setItem('user', JSON.stringify(user)); init(); }
        else toast('AI Evaluation failed.');
    } catch (e) { toast('AI Engine offline.'); }
    btn.disabled = false; btn.innerHTML = 'Analyze Resume';
};

window.createPost = async function() {
    const t = document.getElementById('postTitle').value, c = document.getElementById('postContent').value;
    if (!c.trim()) return toast('Write a narrative first!');
    try {
        const r = await fetch(`${API}/api/posts/`, { method: 'POST', headers: H(), body: JSON.stringify({ title: t || null, content: c }) });
        if (r.ok) { document.getElementById('postTitle').value = ''; document.getElementById('postContent').value = ''; document.getElementById('postModal').classList.remove('active'); toast('Identity verified. Post broadcasted!'); loadPosts(); }
    } catch (e) { toast('Broadcast failed.'); }
};

window.deletePost = async function(id) { if (confirm('Delete professional update?')) { await fetch(`${API}/api/posts/${id}`, { method: 'DELETE', headers: H() }); loadPosts(); } };
window.toggleLike = async function(id) { await fetch(`${API}/api/posts/${id}/like`, { method: 'POST', headers: H() }); loadPosts(); };
window.updateProfile = async function() {
    const data = { name: document.getElementById('profileName').value, batch: document.getElementById('profileBatch').value, branch: document.getElementById('profileBranch').value, company: document.getElementById('profileCompany').value, bio: document.getElementById('profileBio').value };
    const r = await fetch(`${API}/api/users/me`, { method: 'PUT', headers: H(), body: JSON.stringify(data) });
    if (r.ok) { const d = await r.json(); Object.assign(user, d.user); localStorage.setItem('user', JSON.stringify(user)); init(); toast('Digital Identity Synced!'); }
};

window.uploadProfilePic = async function() {
    const f = document.getElementById('picInput'); if (!f || !f.files[0]) return;
    const formData = new FormData(); formData.append('file', f.files[0]);
    try {
        const r = await fetch(`${API}/api/users/profile-picture/upload`, { method: 'POST', headers: { 'Authorization': `Bearer ${token}` }, body: formData });
        if (r.ok) { const d = await r.json(); user.profile_picture = d.profile_picture; localStorage.setItem('user', JSON.stringify(user)); init(); toast('Avatar updated!'); }
    } catch (e) { toast('Error uploading image.'); }
};

window.removeProfilePic = async function() {
    if (confirm('Revert to initial-based avatar?')) {
        const r = await fetch(`${API}/api/users/profile-picture/remove`, { method: 'DELETE', headers: H() });
        if (r.ok) { user.profile_picture = null; localStorage.setItem('user', JSON.stringify(user)); init(); toast('Personal photo removed.'); }
    }
}

document.addEventListener('DOMContentLoaded', () => { init(); const p = new URLSearchParams(window.location.search); const t = p.get('tab'); if (t) showTab(t); else showTab('feed'); });
