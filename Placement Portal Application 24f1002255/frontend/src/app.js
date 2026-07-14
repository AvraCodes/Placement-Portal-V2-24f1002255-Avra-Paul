// ============================================================
// app.js - Creates and mounts the Vue application
//
// This file runs LAST (loaded last in index.html), so all the
// view components (LoginPage, RegisterPage, etc.) and all the
// API helper functions (from api.js) are already defined as
// global variables when this file runs.
// ============================================================

// The root component is the main application.
// It decides which page (view) to show based on the 'page' variable.
var App = {

  // data() is the component's reactive state
  data: function() {
    // If the user already has a saved token, go straight to their dashboard
    var startPage = 'login';
    if (store.token && store.role) {
      startPage = store.role;  // 'admin', 'company', or 'student'
    }
    return {
      page: startPage,
      store: store  // make the global store reactive so the navbar updates
    };
  },

  // Register child components so we can use them in the template
  components: {
    LoginPage:    LoginPage,
    RegisterPage: RegisterPage,
    AdminPage:    AdminPage,
    CompanyPage:  CompanyPage,
    StudentPage:  StudentPage
  },

  methods: {
    // Switch the current page (used by login/register to redirect after success)
    navigate: function(page) {
      this.page = page;
    },

    // Log out the current user and go back to login
    logout: function() {
      clearAuth();  // clears token from memory and localStorage
      this.page = 'login';
      this.store = store; // refresh the reactive store reference
    }
  },

  // The root template renders the correct page component
  // based on the 'page' variable.
  template: `
    <div>
      <!-- Login page - shown when not authenticated -->
      <login-page
        v-if="page === 'login'"
        @navigate="navigate">
      </login-page>

      <!-- Register page - for new students/companies -->
      <register-page
        v-else-if="page === 'register'"
        @navigate="navigate">
      </register-page>

      <!-- Admin dashboard - only for admin role -->
      <admin-page
        v-else-if="page === 'admin'"
        @logout="logout">
      </admin-page>

      <!-- Company dashboard - only for company role -->
      <company-page
        v-else-if="page === 'company'"
        @logout="logout">
      </company-page>

      <!-- Student dashboard - only for student role -->
      <student-page
        v-else-if="page === 'student'"
        @logout="logout">
      </student-page>
    </div>
  `
};

// Create and mount the Vue app on the #app div in index.html
Vue.createApp(App).mount('#app');
