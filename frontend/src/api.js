// ============================================================
// api.js - All API calls and auth state management
// This file is loaded as a regular <script> tag, so everything
// here is a global variable available in all other script files.
// ============================================================

// --- Auth State ---
// These values are saved to localStorage so the user stays logged in after a page refresh.
var store = {
  token: localStorage.getItem('ppa_token') || '',
  role: localStorage.getItem('ppa_role') || '',
  username: localStorage.getItem('ppa_username') || '',
  userId: localStorage.getItem('ppa_userId') || ''
};

// Save login credentials to memory and localStorage
function setAuth(token, user) {
  store.token    = token;
  store.role     = user.role;
  store.username = user.username;
  store.userId   = String(user.id);
  localStorage.setItem('ppa_token',    token);
  localStorage.setItem('ppa_role',     user.role);
  localStorage.setItem('ppa_username', user.username);
  localStorage.setItem('ppa_userId',   String(user.id));
}

// Clear credentials on logout
function clearAuth() {
  store.token = store.role = store.username = store.userId = '';
  localStorage.removeItem('ppa_token');
  localStorage.removeItem('ppa_role');
  localStorage.removeItem('ppa_username');
  localStorage.removeItem('ppa_userId');
}

// --- Base HTTP helper ---
// Automatically attaches the JWT token as a Bearer header.
// Throws the error response body if the request fails.
async function request(path, options) {
  var opts = options || {};
  var headers = { 'Content-Type': 'application/json' };
  if (store.token) {
    headers['Authorization'] = 'Bearer ' + store.token;
  }
  var res = await fetch('/api' + path, Object.assign({ headers: headers }, opts));
  var data = {};
  try { data = await res.json(); } catch (e) {}
  if (res.status === 401) {
    clearAuth();
    window.location.reload();
  }
  if (!res.ok) throw data;
  return data;
}

// --- Auth API calls ---
function apiLogin(username, password) {
  return request('/auth/login', { method: 'POST', body: JSON.stringify({ username: username, password: password }) });
}
function apiRegister(data) {
  return request('/auth/register', { method: 'POST', body: JSON.stringify(data) });
}

// --- Admin API calls ---
function adminDashboard()        { return request('/admin/dashboard'); }
function adminGetCompanies()     { return request('/admin/companies'); }
function adminApproveCompany(id) { return request('/admin/companies/' + id + '/approve', { method: 'PUT' }); }
function adminRejectCompany(id)  { return request('/admin/companies/' + id + '/reject',  { method: 'PUT' }); }
function adminBlacklistCompany(id){ return request('/admin/companies/' + id + '/blacklist', { method: 'PUT' }); }
function adminGetStudents()      { return request('/admin/students'); }
function adminBlacklistStudent(id){ return request('/admin/students/' + id + '/blacklist', { method: 'PUT' }); }
function adminGetDrives()        { return request('/admin/drives'); }
function adminApproveDrive(id)   { return request('/admin/drives/' + id + '/approve', { method: 'PUT' }); }
function adminRejectDrive(id)    { return request('/admin/drives/' + id + '/reject',  { method: 'PUT' }); }
function adminCloseDrive(id)     { return request('/admin/drives/' + id + '/close',   { method: 'PUT' }); }
function adminGetApplications()  { return request('/admin/applications'); }
function adminSearch(q, type)    { return request('/admin/search?q=' + encodeURIComponent(q) + '&type=' + type); }

// --- Company API calls ---
function companyGetProfile()            { return request('/company/profile'); }
function companyUpdateProfile(data)     { return request('/company/profile', { method: 'PUT', body: JSON.stringify(data) }); }
function companyGetDrives()             { return request('/company/drives'); }
function companyCreateDrive(data)       { return request('/company/drives', { method: 'POST', body: JSON.stringify(data) }); }
function companyGetApplicants(driveId)  { return request('/company/drives/' + driveId + '/applications'); }
function companyUpdateStatus(appId, status) { return request('/company/applications/' + appId + '/status', { method: 'PUT', body: JSON.stringify({ status: status }) }); }
function companyCloseDrive(driveId)     { return request('/company/drives/' + driveId + '/close', { method: 'PUT' }); }

// --- Student API calls ---
function studentGetProfile()         { return request('/student/profile'); }
function studentUpdateProfile(data)  { return request('/student/profile', { method: 'PUT', body: JSON.stringify(data) }); }
function studentGetDrives()          { return request('/student/drives'); }
function studentGetApplications()    { return request('/student/applications'); }
function studentApply(driveId)       { return request('/student/drives/' + driveId + '/apply', { method: 'POST' }); }
function studentGetHistory()         { return request('/student/history'); }
function studentExportCSV()          { return request('/student/history/export', { method: 'POST' }); }
function studentUploadResume(formData) {
  // Resume upload uses FormData so we cannot use JSON headers
  return fetch('/api/student/profile/resume', {
    method: 'POST',
    headers: { 'Authorization': 'Bearer ' + store.token },
    body: formData
  }).then(function(r) { return r.json(); });
}

// --- Small helper to format dates nicely ---
function fmtDate(d) {
  if (!d) return '-';
  return new Date(d).toLocaleDateString();
}

// --- Map status string to Bootstrap badge color ---
function statusClass(s) {
  var map = { pending:'warning', approved:'success', rejected:'danger', closed:'secondary',
              applied:'primary', shortlisted:'info', selected:'success', active:'success', inactive:'danger' };
  return 'badge bg-' + (map[s] || 'secondary');
}
