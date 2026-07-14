// ============================================================
// login.js - Login page component
// Defined as a global variable so app.js can use it directly.
// ============================================================

var LoginPage = {
  // data() returns the component's local state
  data: function() {
    return {
      username: '',
      password: '',
      error: '',
      loading: false
    };
  },
  emits: ['navigate'],
  methods: {
    // Called when the login form is submitted
    async handleLogin() {
      this.loading = true;
      this.error = '';
      try {
        var result = await apiLogin(this.username, this.password);
        // Save the token and user info to localStorage via setAuth()
        setAuth(result.token, result.user);
        // Tell the parent app to go to the user's dashboard
        this.$emit('navigate', result.user.role);
      } catch (err) {
        this.error = err.error || 'Login failed. Please check your credentials.';
      } finally {
        this.loading = false;
      }
    }
  },
  template: `
    <div class="d-flex align-items-center justify-content-center" style="min-height:100vh;">
      <div style="width:100%; max-width:400px;" class="p-3">

        <div class="text-center mb-4">
          <h3><i class="bi bi-briefcase-fill text-primary"></i> Placement Portal</h3>
          <p class="text-muted small">Sign in to continue</p>
        </div>

        <div class="card shadow-sm">
          <div class="card-body p-4">

            <!-- Show error if login fails -->
            <div v-if="error" class="alert alert-danger py-2 small">{{ error }}</div>

            <form @submit.prevent="handleLogin">
              <div class="mb-3">
                <label class="form-label">Username</label>
                <input type="text" class="form-control" v-model="username"
                       placeholder="Enter username" required autocomplete="username">
              </div>
              <div class="mb-3">
                <label class="form-label">Password</label>
                <input type="password" class="form-control" v-model="password"
                       placeholder="Enter password" required autocomplete="current-password">
              </div>
              <button type="submit" class="btn btn-primary w-100" :disabled="loading">
                <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
                {{ loading ? 'Signing in...' : 'Sign In' }}
              </button>
            </form>

            <p class="text-center mt-3 mb-0 small">
              New here?
              <a href="#" @click.prevent="$emit('navigate', 'register')">Register as student or company</a>
            </p>

            <!-- Demo credentials hint for evaluators -->
            <div class="mt-3 p-2 bg-light rounded small text-muted text-center">
              Admin login: <strong>admin</strong> / <strong>admin123</strong>
            </div>

          </div>
        </div>
      </div>
    </div>
  `
};
