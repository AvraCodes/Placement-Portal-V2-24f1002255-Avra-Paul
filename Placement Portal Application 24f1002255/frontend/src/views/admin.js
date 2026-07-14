// ============================================================
// admin.js - Admin dashboard component
// Tabs: Overview | Companies | Students | Drives | Applications | Search
// ============================================================

var AdminPage = {
  data: function() {
    return {
      tab: 'overview',          // which tab is active
      stats: {},                // dashboard summary numbers
      companies: [],            // list of all companies
      students: [],             // list of all students
      drives: [],               // list of all placement drives
      applications: [],         // list of all applications
      searchQuery: '',
      searchType: 'students',   // 'students' or 'companies'
      searchResults: [],
      msg: '',                  // success/error message
      loading: false,
      store: store              // expose global store so template can access store.username
    };
  },
  // created() runs once when the component is first mounted
  async created() {
    await this.loadOverview();
  },
  methods: {
    // These wrapper methods expose global helper functions to the Vue template
    fmtDate: function(d) { return fmtDate(d); },
    statusClass: function(s) { return statusClass(s); },

    // Switch tab and load its data if not loaded yet
    async setTab(t) {
      this.tab = t;
      this.msg = '';
      if (t === 'overview')      await this.loadOverview();
      if (t === 'companies')     await this.loadCompanies();
      if (t === 'students')      await this.loadStudents();
      if (t === 'drives')        await this.loadDrives();
      if (t === 'applications')  await this.loadApplications();
    },

    async loadOverview() {
      try { this.stats = await adminDashboard(); } catch(e) {}
    },
    async loadCompanies() {
      try { this.companies = await adminGetCompanies(); } catch(e) {}
    },
    async loadStudents() {
      try { this.students = await adminGetStudents(); } catch(e) {}
    },
    async loadDrives() {
      try { this.drives = await adminGetDrives(); } catch(e) {}
    },
    async loadApplications() {
      try { this.applications = await adminGetApplications(); } catch(e) {}
    },

    // --- Company actions ---
    async approveCompany(id) {
      try { await adminApproveCompany(id); this.msg = 'Company approved.'; await this.loadCompanies(); }
      catch(e) { this.msg = 'Error: ' + (e.error || 'failed'); }
    },
    async rejectCompany(id) {
      try { await adminRejectCompany(id); this.msg = 'Company rejected.'; await this.loadCompanies(); }
      catch(e) { this.msg = 'Error: ' + (e.error || 'failed'); }
    },
    async blacklistCompany(id) {
      if (!confirm('Toggle blacklist for this company?')) return;
      try { await adminBlacklistCompany(id); this.msg = 'Done.'; await this.loadCompanies(); }
      catch(e) { this.msg = 'Error: ' + (e.error || 'failed'); }
    },

    // --- Student actions ---
    async blacklistStudent(id) {
      if (!confirm('Toggle blacklist for this student?')) return;
      try { await adminBlacklistStudent(id); this.msg = 'Done.'; await this.loadStudents(); }
      catch(e) { this.msg = 'Error: ' + (e.error || 'failed'); }
    },

    // --- Drive actions ---
    async approveDrive(id) {
      try { await adminApproveDrive(id); this.msg = 'Drive approved.'; await this.loadDrives(); }
      catch(e) { this.msg = 'Error: ' + (e.error || 'failed'); }
    },
    async rejectDrive(id) {
      try { await adminRejectDrive(id); this.msg = 'Drive rejected.'; await this.loadDrives(); }
      catch(e) { this.msg = 'Error: ' + (e.error || 'failed'); }
    },
    async closeDrive(id) {
      if (!confirm('Close this drive?')) return;
      try { await adminCloseDrive(id); this.msg = 'Drive closed.'; await this.loadDrives(); }
      catch(e) { this.msg = 'Error: ' + (e.error || 'failed'); }
    },

    // --- Search ---
    async doSearch() {
      if (!this.searchQuery.trim()) return;
      try {
        var r = await adminSearch(this.searchQuery, this.searchType);
        this.searchResults = r.results || [];
      } catch(e) { this.msg = 'Search failed.'; }
    }
  },
  template: `
    <div>
      <!-- Tab navigation bar -->
      <nav class="navbar navbar-expand navbar-light bg-white border-bottom px-4">
        <span class="navbar-brand fw-bold text-primary me-4">
          <i class="bi bi-briefcase-fill me-1"></i>Admin Panel
        </span>
        <ul class="navbar-nav me-auto gap-1">
          <li class="nav-item" v-for="t in ['overview','companies','students','drives','applications','search']" :key="t">
            <button class="btn btn-sm" :class="tab===t?'btn-primary':'btn-outline-secondary'" @click="setTab(t)">
              {{ t.charAt(0).toUpperCase() + t.slice(1) }}
            </button>
          </li>
        </ul>
        <span class="text-muted small me-3">{{ store.username }}</span>
        <button class="btn btn-sm btn-outline-danger" @click="$emit('logout')">Logout</button>
      </nav>

      <div class="container-fluid px-4 py-3">
        <!-- Feedback message -->
        <div v-if="msg" class="alert alert-info py-2 small">{{ msg }}</div>

        <!-- ===== OVERVIEW TAB ===== -->
        <div v-if="tab === 'overview'">
          <h5 class="mb-3">Dashboard Overview</h5>
          <div class="row g-3">
            <div class="col-6 col-md-3">
              <div class="card text-center p-3 border-primary">
                <div class="fs-2 fw-bold text-primary">{{ stats.total_students || 0 }}</div>
                <div class="text-muted small">Students</div>
              </div>
            </div>
            <div class="col-6 col-md-3">
              <div class="card text-center p-3 border-success">
                <div class="fs-2 fw-bold text-success">{{ stats.total_companies || 0 }}</div>
                <div class="text-muted small">Companies</div>
              </div>
            </div>
            <div class="col-6 col-md-3">
              <div class="card text-center p-3 border-warning">
                <div class="fs-2 fw-bold text-warning">{{ stats.total_drives || 0 }}</div>
                <div class="text-muted small">Drives</div>
              </div>
            </div>
            <div class="col-6 col-md-3">
              <div class="card text-center p-3 border-info">
                <div class="fs-2 fw-bold text-info">{{ stats.total_applications || 0 }}</div>
                <div class="text-muted small">Applications</div>
              </div>
            </div>
            <div class="col-6 col-md-3">
              <div class="card text-center p-3">
                <div class="fs-2 fw-bold text-danger">{{ stats.pending_companies || 0 }}</div>
                <div class="text-muted small">Pending Companies</div>
              </div>
            </div>
            <div class="col-6 col-md-3">
              <div class="card text-center p-3">
                <div class="fs-2 fw-bold text-danger">{{ stats.pending_drives || 0 }}</div>
                <div class="text-muted small">Pending Drives</div>
              </div>
            </div>
            <div class="col-6 col-md-3">
              <div class="card text-center p-3">
                <div class="fs-2 fw-bold text-success">{{ stats.selected_students || 0 }}</div>
                <div class="text-muted small">Selected Students</div>
              </div>
            </div>
            <div class="col-6 col-md-3">
              <div class="card text-center p-3">
                <div class="fs-2 fw-bold text-success">{{ stats.approved_drives || 0 }}</div>
                <div class="text-muted small">Approved Drives</div>
              </div>
            </div>
          </div>
        </div>

        <!-- ===== COMPANIES TAB ===== -->
        <div v-if="tab === 'companies'">
          <h5 class="mb-3">Company Registrations</h5>
          <div class="table-responsive">
            <table class="table table-bordered table-sm">
              <thead class="table-light">
                <tr>
                  <th>Company</th><th>Username</th><th>Industry</th>
                  <th>Status</th><th>Active</th><th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="companies.length === 0"><td colspan="6" class="text-center text-muted">No companies yet.</td></tr>
                <tr v-for="c in companies" :key="c.id">
                  <td>{{ c.company_name }}</td>
                  <td>{{ c.username }}</td>
                  <td>{{ c.industry || '-' }}</td>
                  <td><span :class="statusClass(c.approval_status)">{{ c.approval_status }}</span></td>
                  <td><span :class="statusClass(c.is_active ? 'active' : 'inactive')">{{ c.is_active ? 'Yes' : 'No' }}</span></td>
                  <td class="text-nowrap">
                    <button v-if="c.approval_status === 'pending'" class="btn btn-xs btn-success btn-sm me-1" @click="approveCompany(c.id)">Approve</button>
                    <button v-if="c.approval_status === 'pending'" class="btn btn-xs btn-danger btn-sm me-1"  @click="rejectCompany(c.id)">Reject</button>
                    <button class="btn btn-sm btn-outline-secondary" @click="blacklistCompany(c.user_id)">
                      {{ c.is_active ? 'Blacklist' : 'Unblacklist' }}
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- ===== STUDENTS TAB ===== -->
        <div v-if="tab === 'students'">
          <h5 class="mb-3">Registered Students</h5>
          <div class="table-responsive">
            <table class="table table-bordered table-sm">
              <thead class="table-light">
                <tr>
                  <th>Name</th><th>Username</th><th>Branch</th>
                  <th>CGPA</th><th>Year</th><th>Active</th><th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="students.length === 0"><td colspan="7" class="text-center text-muted">No students yet.</td></tr>
                <tr v-for="s in students" :key="s.id">
                  <td>{{ s.full_name }}</td>
                  <td>{{ s.username }}</td>
                  <td>{{ s.branch }}</td>
                  <td>{{ s.cgpa }}</td>
                  <td>{{ s.year }}</td>
                  <td><span :class="statusClass(s.is_active ? 'active' : 'inactive')">{{ s.is_active ? 'Yes' : 'No' }}</span></td>
                  <td>
                    <button class="btn btn-sm btn-outline-secondary" @click="blacklistStudent(s.user_id)">
                      {{ s.is_active ? 'Blacklist' : 'Unblacklist' }}
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- ===== DRIVES TAB ===== -->
        <div v-if="tab === 'drives'">
          <h5 class="mb-3">Placement Drives</h5>
          <div class="table-responsive">
            <table class="table table-bordered table-sm">
              <thead class="table-light">
                <tr>
                  <th>Drive</th><th>Company</th><th>Job Title</th>
                  <th>Deadline</th><th>Status</th><th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="drives.length === 0"><td colspan="6" class="text-center text-muted">No drives yet.</td></tr>
                <tr v-for="d in drives" :key="d.id">
                  <td>{{ d.drive_name }}</td>
                  <td>{{ d.company_name }}</td>
                  <td>{{ d.job_title }}</td>
                  <td>{{ fmtDate(d.application_deadline) }}</td>
                  <td><span :class="statusClass(d.status)">{{ d.status }}</span></td>
                  <td class="text-nowrap">
                    <button v-if="d.status === 'pending'" class="btn btn-sm btn-success me-1" @click="approveDrive(d.id)">Approve</button>
                    <button v-if="d.status === 'pending'" class="btn btn-sm btn-danger me-1"  @click="rejectDrive(d.id)">Reject</button>
                    <button v-if="d.status === 'approved'" class="btn btn-sm btn-secondary" @click="closeDrive(d.id)">Close</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- ===== APPLICATIONS TAB ===== -->
        <div v-if="tab === 'applications'">
          <h5 class="mb-3">All Applications</h5>
          <div class="table-responsive">
            <table class="table table-bordered table-sm">
              <thead class="table-light">
                <tr>
                  <th>Student</th><th>Branch</th><th>CGPA</th>
                  <th>Company</th><th>Drive</th><th>Date</th><th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="applications.length === 0"><td colspan="7" class="text-center text-muted">No applications yet.</td></tr>
                <tr v-for="a in applications" :key="a.id">
                  <td>{{ a.student_name }}</td>
                  <td>{{ a.student_branch }}</td>
                  <td>{{ a.student_cgpa }}</td>
                  <td>{{ a.company_name }}</td>
                  <td>{{ a.drive_name }}</td>
                  <td>{{ fmtDate(a.application_date) }}</td>
                  <td><span :class="statusClass(a.status)">{{ a.status }}</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- ===== SEARCH TAB ===== -->
        <div v-if="tab === 'search'">
          <h5 class="mb-3">Search</h5>
          <div class="row g-2 mb-3">
            <div class="col-auto">
              <select class="form-select form-select-sm" v-model="searchType">
                <option value="students">Students</option>
                <option value="companies">Companies</option>
              </select>
            </div>
            <div class="col">
              <input type="text" class="form-control form-control-sm"
                     v-model="searchQuery" placeholder="Type to search..." @keyup.enter="doSearch">
            </div>
            <div class="col-auto">
              <button class="btn btn-sm btn-primary" @click="doSearch">Search</button>
            </div>
          </div>
          <div class="table-responsive">
            <table class="table table-bordered table-sm" v-if="searchResults.length">
              <thead class="table-light">
                <tr>
                  <th v-if="searchType === 'students'">Name</th>
                  <th v-if="searchType === 'companies'">Company</th>
                  <th>Username</th>
                  <th v-if="searchType === 'students'">Branch</th>
                  <th v-if="searchType === 'students'">CGPA</th>
                  <th v-if="searchType === 'companies'">Industry</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="r in searchResults" :key="r.id">
                  <td>{{ searchType === 'students' ? r.full_name : r.company_name }}</td>
                  <td>{{ r.username }}</td>
                  <td v-if="searchType === 'students'">{{ r.branch }}</td>
                  <td v-if="searchType === 'students'">{{ r.cgpa }}</td>
                  <td v-if="searchType === 'companies'">{{ r.industry || '-' }}</td>
                  <td>
                    <span v-if="searchType === 'companies'" :class="statusClass(r.approval_status)">{{ r.approval_status }}</span>
                    <span v-else :class="statusClass(r.is_active ? 'active' : 'inactive')">{{ r.is_active ? 'Active' : 'Blacklisted' }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
            <p v-else-if="searchQuery" class="text-muted small">No results found.</p>
          </div>
        </div>

      </div>
    </div>
  `
};
