const API = window.location.origin, token = localStorage.getItem('token'), user = JSON.parse(localStorage.getItem('user') || 'null');
if (!token || !user) { if (!['/login', '/register', '/'].includes(window.location.pathname)) location.href = '/login'; }

function H() { return { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` }; }
function toast(m) { const c = document.getElementById('toastContainer'); const d = document.createElement('div'); d.className = 'ln-toast'; d.textContent = m; c.appendChild(d); setTimeout(() => d.remove(), 3000); }
function loadingState(title, subtitle = 'This can take a moment on the first production request.') {
    return `<div class="jec-loading-state">
        <div class="jec-loader-icon"></div>
        <div class="jec-loading-title">${title}</div>
        <div class="jec-loading-subtitle">${subtitle}</div>
    </div>`;
}
function setBtnBusy(btn, label) {
    if (!btn) return null;
    const original = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${label}`;
    return original;
}
function restoreBtn(btn, original) {
    if (!btn || original === null) return;
    btn.disabled = false;
    btn.innerHTML = original;
}

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
    const c = document.getElementById('postsContainer'); if (!c) return;
    c.innerHTML = loadingState('Loading community feed', 'Fetching posts, comments, and reactions...');
    try {
        const r = await fetch(`${API}/api/posts/`, { headers: H() });
        const ps = await r.json();
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
                    <button class="ln-post-action" onclick="toggleLike(${p.id}, this)"><i class="fas fa-thumbs-up"></i> ${p.like_count || ''} Like</button>
                    <button class="ln-post-action" onclick="toggleComments(${p.id})"><i class="fas fa-comment"></i> ${(p.comments && p.comments.length) || ''} Comment</button>
                    ${(p.author_id === user.id || user.role === 'admin') ? `<button class="ln-post-action" style="color:var(--jec-maroon);" onclick="deletePost(${p.id}, this)"><i class="fas fa-trash"></i></button>` : ''}
                </div>
                <div id="comments-${p.id}" style="display:none; border-top:1px solid #eee; padding-top:10px; margin-top:10px;">
                    <div style="display:flex; gap:10px; margin-bottom:15px;">
                        <input type="text" id="comment-input-${p.id}" class="jec-input" placeholder="Add a comment..." style="flex:1;">
                        <button class="jec-btn-primary" onclick="addComment(${p.id}, this)">Post</button>
                    </div>
                    <div class="comments-list">
                        ${(p.comments || []).map(c => `
                            <div style="background:#f3f2ef; padding:10px; border-radius:8px; margin-bottom:10px;">
                                <div style="font-weight:600; font-size:0.9rem;">${c.author_name} <span style="font-weight:400; font-size:0.8rem; color:#666;">${timeAgo(c.created_at)}</span>
                                ${(c.author_id === user.id || user.role === 'admin') ? `<button onclick="deleteComment(${c.id}, this)" style="float:right; background:none; border:none; color:#800000; cursor:pointer;"><i class="fas fa-trash"></i></button>` : ''}
                                </div>
                                <div style="font-size:0.95rem; margin-top:4px;">${c.content}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `).join('');
    } catch (e) {
        c.innerHTML = '<div class="jec-loading-state">Could not load community feed. Please try again.</div>';
        toast('Failed to load community feed.');
    }
};

window.loadDirectory = async function() {
    const s = document.getElementById('searchName').value, b = document.getElementById('searchBatch').value, c = document.getElementById('searchCompany').value;
    let url = `${API}/api/users/directory?`;
    if (s) url += `search=${encodeURIComponent(s)}&`; if (b) url += `batch=${encodeURIComponent(b)}&`; if (c) url += `company=${encodeURIComponent(c)}&`;
    const container = document.getElementById('directoryContainer');
    container.innerHTML = loadingState('Searching alumni registry', 'Matching names, batch, and company filters...');
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
                <div class="ln-member-info" style="cursor:pointer;" onclick="viewProfile(${a.id}, '${a.name.replace(/'/g,"\\'")}', '${a.role}', '${a.company||"JEC Alumni"}', '${a.branch||"Engineer"}', '${(a.bio||"Dedicated member of the JEC community.").replace(/'/g,"\\'").replace(/\n/g," ")}', '${(a.skills||"All-rounder").replace(/'/g,"\\'")}', '${a.profile_picture || ""}')">
                    <div class="ln-member-name">${a.name}</div>
                    <div class="ln-member-detail">${a.company || 'JEC Alumni'} · ${a.branch || '—'} · Batch ${a.batch || '—'}</div>
                </div>
                <div style="display:flex; gap:8px;">
                    <button class="jec-btn-primary jec-btn-sm" onclick="sendConnection(${a.id}, this)">Connect</button>
                </div>
            </div>
        `).join('');
    } catch (e) {
        container.innerHTML = '<div class="jec-loading-state">Search failed. Please try again.</div>';
        toast('Search Engine offline.');
    }
};

window.viewProfile = function(id, name, role, company, branch, bio, skills, pic) {
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
    window.currentChatUserId = id;
    window.currentChatUserName = name;
    window.currentChatUserRole = role;
    window.currentChatUserPic = pic || '';
    const btn = document.getElementById('pModalMessageBtn');
    if (btn) btn.style.display = (id !== user.id) ? 'inline-block' : 'none';
    document.getElementById('profileModal').classList.add('active');
};

window.sendConnection = async function(id, btn) {
    const original = setBtnBusy(btn, 'Sending');
    try {
        const r = await fetch(`${API}/api/connections/`, { method: 'POST', headers: H(), body: JSON.stringify({ receiver_id: id }) });
        const data = await r.json().catch(() => ({}));
        if (r.ok) {
            btn.innerHTML = '<i class="fas fa-check"></i> Sent';
            btn.disabled = true;
            toast('Connection request sent!');
            loadPendingConnectionRequests();
            return;
        }
        if ((data.detail || '').toLowerCase().includes('already')) {
            btn.innerHTML = '<i class="fas fa-check"></i> Sent';
            btn.disabled = true;
            toast('Connection request already exists.');
            return;
        }
        restoreBtn(btn, original);
        toast(data.detail || 'Action failed.');
    } catch (e) {
        restoreBtn(btn, original);
        toast('Action failed.');
    }
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
                    <button class="jec-btn-primary jec-btn-sm" style="padding:4px 8px; border-radius:4px;" onclick="respondReq(${req.id},'accepted', this)"><i class="fas fa-check"></i></button>
                    <button class="jec-btn-primary jec-btn-sm" style="background:#eee; color:#666; padding:4px 8px; border-radius:4px;" onclick="respondReq(${req.id},'rejected', this)"><i class="fas fa-times"></i></button>
                </div>
            </div>
        `).join('');
    } catch (e) { }
};

window.respondReq = async function(id, status, btn) {
    const original = setBtnBusy(btn, status === 'accepted' ? 'Accepting' : 'Rejecting');
    const group = btn ? btn.parentElement : null;
    if (group) group.querySelectorAll('button').forEach(b => b.disabled = true);
    try {
        const r = await fetch(`${API}/api/connections/${id}/status`, { method: 'PUT', headers: H(), body: JSON.stringify({ status }) });
        if (r.ok) {
            if (group) group.innerHTML = `<span style="font-size:0.75rem; font-weight:800; color:var(--jec-maroon);">${status === 'accepted' ? 'Accepted' : 'Rejected'}</span>`;
            toast(`Professional request ${status}.`);
            loadPendingConnectionRequests();
            loadConnectionCount();
            return;
        }
        restoreBtn(btn, original);
        if (group) group.querySelectorAll('button').forEach(b => b.disabled = false);
        toast('Unable to update invitation.');
    } catch (e) {
        restoreBtn(btn, original);
        if (group) group.querySelectorAll('button').forEach(b => b.disabled = false);
        toast('Error synchronizing invitation.');
    }
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

window.createPost = async function(btn) {
    const t = document.getElementById('postTitle').value, c = document.getElementById('postContent').value;
    if (!c.trim()) return toast('Write a narrative first!');
    const original = setBtnBusy(btn, 'Broadcasting');
    try {
        const r = await fetch(`${API}/api/posts/`, { method: 'POST', headers: H(), body: JSON.stringify({ title: t || null, content: c }) });
        if (r.ok) { if (btn) btn.innerHTML = '<i class="fas fa-check"></i> Posted'; document.getElementById('postTitle').value = ''; document.getElementById('postContent').value = ''; document.getElementById('postModal').classList.remove('active'); toast('Identity verified. Post broadcasted!'); loadPosts(); return; }
        restoreBtn(btn, original);
    } catch (e) { restoreBtn(btn, original); toast('Broadcast failed.'); }
};

window.deletePost = async function(id, btn) {
    if (!confirm('Delete professional update?')) return;
    const original = setBtnBusy(btn, '');
    try {
        const r = await fetch(`${API}/api/posts/${id}`, { method: 'DELETE', headers: H() });
        if (r.ok) { if (btn) btn.innerHTML = '<i class="fas fa-check"></i>'; loadPosts(); return; }
        restoreBtn(btn, original);
    } catch (e) { restoreBtn(btn, original); toast('Delete failed.'); }
};
window.toggleLike = async function(id, btn) {
    const original = setBtnBusy(btn, 'Updating');
    try {
        const r = await fetch(`${API}/api/posts/${id}/like`, { method: 'POST', headers: H() });
        if (r.ok) { if (btn) btn.innerHTML = '<i class="fas fa-check"></i> Updated'; loadPosts(); return; }
        restoreBtn(btn, original);
    } catch (e) { restoreBtn(btn, original); toast('Could not update like.'); }
};

window.toggleComments = function(id) {
    const el = document.getElementById(`comments-${id}`);
    if (el) el.style.display = el.style.display === 'none' ? 'block' : 'none';
};

window.addComment = async function(id, btn) {
    const input = document.getElementById(`comment-input-${id}`);
    const val = input.value.trim();
    if (!val) return;
    const original = setBtnBusy(btn, 'Posting');
    input.disabled = true;
    try {
        const r = await fetch(`${API}/api/posts/${id}/comment`, { method: 'POST', headers: H(), body: JSON.stringify({ content: val }) });
        if (r.ok) {
            if (btn) btn.innerHTML = '<i class="fas fa-check"></i> Posted';
            toast('Comment added!');
            await loadPosts();
            const el = document.getElementById(`comments-${id}`);
            if (el) el.style.display = 'block';
            return;
        }
        restoreBtn(btn, original);
        input.disabled = false;
    } catch (e) { restoreBtn(btn, original); input.disabled = false; toast('Error adding comment'); }
};

window.deleteComment = async function(cid, btn) {
    if (!confirm('Delete this comment?')) return;
    const original = setBtnBusy(btn, '');
    try {
        const r = await fetch(`${API}/api/posts/comment/${cid}`, { method: 'DELETE', headers: H() });
        if (r.ok) { if (btn) btn.innerHTML = '<i class="fas fa-check"></i>'; toast('Comment deleted'); loadPosts(); return; }
        restoreBtn(btn, original);
    } catch (e) { restoreBtn(btn, original); toast('Error deleting comment'); }
};
window.updateProfile = async function(btn) {
    const original = setBtnBusy(btn, 'Saving');
    const data = { name: document.getElementById('profileName').value, batch: document.getElementById('profileBatch').value, branch: document.getElementById('profileBranch').value, company: document.getElementById('profileCompany').value, bio: document.getElementById('profileBio').value };
    try {
        const r = await fetch(`${API}/api/users/me`, { method: 'PUT', headers: H(), body: JSON.stringify(data) });
        if (r.ok) {
            const d = await r.json();
            if (btn) btn.innerHTML = '<i class="fas fa-check"></i> Saved';
            Object.assign(user, d.user);
            localStorage.setItem('user', JSON.stringify(user));
            init();
            toast('Digital Identity Synced!');
            return;
        }
        restoreBtn(btn, original);
    } catch (e) {
        restoreBtn(btn, original);
        toast('Profile sync failed.');
    }
};

window.uploadProfilePic = async function() {
    const f = document.getElementById('picInput'); if (!f || !f.files[0]) return;
    const formData = new FormData(); formData.append('file', f.files[0]);
    try {
        const r = await fetch(`${API}/api/users/profile-picture/upload`, { method: 'POST', headers: { 'Authorization': `Bearer ${token}` }, body: formData });
        if (r.ok) { const d = await r.json(); user.profile_picture = d.profile_picture; localStorage.setItem('user', JSON.stringify(user)); init(); toast('Avatar updated!'); }
    } catch (e) { toast('Error uploading image.'); }
};

window.removeProfilePic = async function(btn) {
    if (confirm('Revert to initial-based avatar?')) {
        const original = setBtnBusy(btn, 'Removing');
        try {
            const r = await fetch(`${API}/api/users/profile-picture/remove`, { method: 'DELETE', headers: H() });
            if (r.ok) { if (btn) btn.innerHTML = '<i class="fas fa-check"></i> Removed'; user.profile_picture = null; localStorage.setItem('user', JSON.stringify(user)); init(); toast('Personal photo removed.'); return; }
            restoreBtn(btn, original);
        } catch (e) {
            restoreBtn(btn, original);
            toast('Could not remove photo.');
        }
    }
}

window.currentChatUserId = null;
window.currentChatUserName = null;
window.currentChatUserRole = null;
window.currentChatUserPic = null;
window.allConversations = [];
window.chatRefreshTimer = null;

// ===== Render message bubbles (shared between inline and overlay) =====
function renderBubbles(msgs, container) {
    if (!msgs.length) {
        container.innerHTML = `
            <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; color:#999; text-align:center; padding:40px;">
                <i class="fas fa-comment-dots" style="font-size:2.5rem; color:#ddd; margin-bottom:12px;"></i>
                <p style="font-weight:600; font-size:0.95rem; color:#888;">No messages yet</p>
                <p style="font-size:0.8rem; margin-top:4px;">Send a message to start the conversation!</p>
            </div>`;
        return;
    }
    container.innerHTML = msgs.map(m => {
        const isSent = m.sender_id === user.id;
        const t = m.created_at ? new Date(m.created_at) : null;
        const timeStr = t ? t.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';
        return `<div class="chat-bubble ${isSent ? 'sent' : 'received'}">
            ${m.content}
            <span class="chat-bubble-time">${timeStr}</span>
        </div>`;
    }).join('');
    container.scrollTop = container.scrollHeight;
}

// ===== Load conversations list =====
window.loadConversations = async function() {
    const c = document.getElementById('conversationsContainer');
    if (c) c.innerHTML = loadingState('Loading conversations', 'Syncing your alumni messages...');
    try {
        const r = await fetch(`${API}/api/messages/conversations`, { headers: H() });
        const convs = await r.json();
        window.allConversations = convs;
        renderConversationsList(convs);
    } catch (e) {
        const c = document.getElementById('conversationsContainer');
        if (c) c.innerHTML = `
            <div class="chat-empty-state">
                <i class="fas fa-users"></i>
                <p>Connect with alumni to start chatting!</p>
            </div>`;
    }
};

function renderConversationsList(convs) {
    const c = document.getElementById('conversationsContainer');
    if (!c) return;
    if (!convs.length) {
        c.innerHTML = `
            <div class="chat-empty-state">
                <i class="fas fa-user-friends" style="font-size:2rem; color:#ddd; margin-bottom:10px;"></i>
                <p style="font-weight:600; color:#888;">No conversations yet</p>
                <p style="font-size:0.8rem; margin-top:4px;">Visit the Alumni directory to connect and start chatting.</p>
            </div>`;
        return;
    }
    c.innerHTML = convs.map(cv => {
        const isActive = window.currentChatUserId === cv.user_id;
        const preview = cv.last_message ? (cv.last_message.length > 40 ? cv.last_message.slice(0, 40) + '…' : cv.last_message) : 'Start a conversation…';
        const t = cv.last_message_time ? new Date(cv.last_message_time) : null;
        const timeStr = t ? timeAgo(cv.last_message_time) : '';
        const pic = cv.profile_picture;
        return `
        <div class="chat-conv-item ${isActive ? 'active' : ''}" onclick="openInlineChat(${cv.user_id}, '${cv.user_name.replace(/'/g,"\\'")}', '${cv.user_role}', '${pic || ''}')">
            <div class="chat-conv-avatar" style="background:${pic ? 'none' : avatarColor(cv.user_name)}">
                ${pic ? `<img src="${pic}" style="width:100%; height:100%; border-radius:50%; object-fit:cover;">` : cv.user_name.charAt(0).toUpperCase()}
            </div>
            <div class="chat-conv-info">
                <div class="chat-conv-name">
                    ${cv.user_name}
                    <span class="chat-conv-role-badge">${cv.user_role}</span>
                </div>
                <div class="chat-conv-preview">${preview}</div>
            </div>
            <div class="chat-conv-meta">
                <span class="chat-conv-time">${timeStr}</span>
                ${cv.unread_count > 0 ? `<span class="chat-unread-badge">${cv.unread_count}</span>` : ''}
            </div>
        </div>`;
    }).join('');
}

// ===== Filter conversations =====
window.filterConversations = function(query) {
    const q = query.toLowerCase().trim();
    if (!q) { renderConversationsList(window.allConversations); return; }
    const filtered = window.allConversations.filter(cv =>
        cv.user_name.toLowerCase().includes(q) || cv.user_role.toLowerCase().includes(q)
    );
    renderConversationsList(filtered);
};

// ===== Open inline chat (Messages tab) =====
window.openInlineChat = async function(userId, userName, userRole, userPic) {
    window.currentChatUserId = userId;
    window.currentChatUserName = userName;
    window.currentChatUserRole = userRole || '';
    window.currentChatUserPic = userPic || '';

    // Update header
    const nameEl = document.getElementById('inlineChatName');
    const roleEl = document.getElementById('inlineChatRole');
    const avatarEl = document.getElementById('inlineChatAvatar');
    if (nameEl) nameEl.textContent = userName;
    if (roleEl) roleEl.textContent = userRole || 'Member';
    if (avatarEl) {
        if (userPic) {
            avatarEl.innerHTML = `<img src="${userPic}" style="width:100%; height:100%; border-radius:50%; object-fit:cover;">`;
            avatarEl.style.background = 'none';
        } else {
            avatarEl.textContent = userName.charAt(0).toUpperCase();
            avatarEl.style.background = avatarColor(userName);
        }
    }

    // Show active view, hide welcome
    document.getElementById('chatWelcome').style.display = 'none';
    document.getElementById('chatActiveView').style.display = 'flex';

    // Mark active in sidebar
    document.querySelectorAll('.chat-conv-item').forEach(el => el.classList.remove('active'));
    // Re-render to highlight
    renderConversationsList(window.allConversations);

    // Load messages
    await loadInlineMessages(userId);

    // Start auto-refresh
    clearInterval(window.chatRefreshTimer);
    window.chatRefreshTimer = setInterval(() => loadInlineMessages(userId, false), 5000);

    // Focus input
    const input = document.getElementById('inlineChatInput');
    if (input) input.focus();
};

// ===== Load messages into inline chat =====
async function loadInlineMessages(userId, showLoader = true) {
    const body = document.getElementById('inlineChatBody');
    if (!body) return;
    if (showLoader) body.innerHTML = loadingState('Loading messages', 'Opening the selected conversation...');
    try {
        const r = await fetch(`${API}/api/messages/${userId}`, { headers: H() });
        const msgs = await r.json();
        const wasAtBottom = body.scrollHeight - body.scrollTop - body.clientHeight < 50;
        renderBubbles(msgs, body);
        if (wasAtBottom) body.scrollTop = body.scrollHeight;
    } catch (e) {
        body.innerHTML = '<div style="text-align:center; padding:20px; color:#888;">Failed to load messages</div>';
    }
}

// ===== Send message from inline chat =====
window.sendInlineMessage = async function(btn) {
    const input = document.getElementById('inlineChatInput');
    const val = input.value.trim();
    if (!val || !window.currentChatUserId) return;
    const original = setBtnBusy(btn, '');
    input.disabled = true;
    input.value = '';
    try {
        const r = await fetch(`${API}/api/messages/`, {
            method: 'POST',
            headers: H(),
            body: JSON.stringify({ receiver_id: window.currentChatUserId, content: val })
        });
        if (r.ok) {
            if (btn) btn.innerHTML = '<i class="fas fa-check"></i>';
            await loadInlineMessages(window.currentChatUserId, false);
            loadConversations(); // refresh sidebar
            input.disabled = false;
            restoreBtn(btn, original);
            input.focus();
            return;
        }
        input.value = val;
        input.disabled = false;
        restoreBtn(btn, original);
    } catch (e) {
        input.value = val;
        input.disabled = false;
        restoreBtn(btn, original);
        toast('Failed to send message');
    }
};

// ===== Pop-out overlay from profile modal =====
window.openChatFromProfile = function() {
    document.getElementById('profileModal').classList.remove('active');
    const overlay = document.getElementById('chatOverlay');
    overlay.style.display = 'flex';
    document.getElementById('chatTitle').textContent = window.currentChatUserName;

    // Set overlay avatar
    const av = document.getElementById('overlayAvatar');
    if (av) {
        if (window.currentChatUserPic) {
            av.innerHTML = `<img src="${window.currentChatUserPic}" style="width:100%; height:100%; border-radius:50%; object-fit:cover;">`;
            av.style.background = 'none';
        } else {
            av.textContent = (window.currentChatUserName || 'U').charAt(0).toUpperCase();
            av.style.background = 'rgba(255,255,255,0.2)';
        }
    }

    loadOverlayMessages(window.currentChatUserId);
};

// ===== Pop-out overlay from inline chat ("minimize") =====
window.minimizeToOverlay = function() {
    const overlay = document.getElementById('chatOverlay');
    overlay.style.display = 'flex';
    document.getElementById('chatTitle').textContent = window.currentChatUserName;
    const av = document.getElementById('overlayAvatar');
    if (av) {
        if (window.currentChatUserPic) {
            av.innerHTML = `<img src="${window.currentChatUserPic}" style="width:100%; height:100%; border-radius:50%; object-fit:cover;">`;
            av.style.background = 'none';
        } else {
            av.textContent = (window.currentChatUserName || 'U').charAt(0).toUpperCase();
            av.style.background = 'rgba(255,255,255,0.2)';
        }
    }
    loadOverlayMessages(window.currentChatUserId);
};

// ===== Expand overlay to inline (Messages tab) =====
window.expandToInline = function() {
    closeChatOverlay();
    showTab('messages');
    if (window.currentChatUserId) {
        setTimeout(() => {
            openInlineChat(window.currentChatUserId, window.currentChatUserName, window.currentChatUserRole, window.currentChatUserPic);
        }, 200);
    }
};

window.closeChatOverlay = function() {
    document.getElementById('chatOverlay').style.display = 'none';
};

// ===== Load messages into overlay =====
async function loadOverlayMessages(userId) {
    const cb = document.getElementById('chatBody');
    cb.innerHTML = loadingState('Loading messages', 'Opening the selected conversation...');
    try {
        const r = await fetch(`${API}/api/messages/${userId}`, { headers: H() });
        const msgs = await r.json();
        renderBubbles(msgs, cb);
    } catch (e) {
        cb.innerHTML = '<div style="text-align:center; padding:20px; color:#888;">Failed to load messages</div>';
    }
}

// ===== Send message from overlay =====
window.sendMessage = async function(btn) {
    const input = document.getElementById('chatInput');
    const val = input.value.trim();
    if (!val || !window.currentChatUserId) return;
    const original = setBtnBusy(btn, '');
    input.disabled = true;
    input.value = '';
    try {
        const r = await fetch(`${API}/api/messages/`, {
            method: 'POST',
            headers: H(),
            body: JSON.stringify({ receiver_id: window.currentChatUserId, content: val })
        });
        if (r.ok) {
            if (btn) btn.innerHTML = '<i class="fas fa-check"></i>';
            loadOverlayMessages(window.currentChatUserId);
            loadConversations();
            input.disabled = false;
            restoreBtn(btn, original);
            input.focus();
            return;
        }
        input.value = val;
        input.disabled = false;
        restoreBtn(btn, original);
    } catch (e) {
        input.value = val;
        input.disabled = false;
        restoreBtn(btn, original);
        toast('Failed to send message');
    }
};

// ===== Tab loading hook =====
const originalShowTab = window.showTab;
window.showTab = function(name) {
    document.querySelectorAll('.jec-tab').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.ln-tab-content').forEach(c => c.classList.remove('active'));
    const cap = name.charAt(0).toUpperCase() + name.slice(1);
    const t = document.getElementById(`tab${cap}`), c = document.getElementById(`content${cap}`);
    if (t) t.classList.add('active'); if (c) c.classList.add('active');
    if (name === 'feed') loadPosts();
    if (name === 'directory') loadDirectory();
    if (name === 'messages') loadConversations();
};

// Close modals on overlay click
['postModal', 'profileModal'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.onclick = (e) => { if (e.target.id === id) el.classList.remove('active'); };
});

document.addEventListener('DOMContentLoaded', () => { init(); const p = new URLSearchParams(window.location.search); const t = p.get('tab'); if (t) showTab(t); else showTab('feed'); });

