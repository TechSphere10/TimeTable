// Supabase Configuration
const SUPABASE_URL = 'https://bkmzyhroignpjebfpqug.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJrbXp5aHJvaWducGplYmZwcXVnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc0MjA1NDUsImV4cCI6MjA3Mjk5NjU0NX0.ICE2eYzFZvz0dtNpAa5YlJTZD-idc2J76wn1ZeHwwck';

// Initialize Supabase client
const supabase = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// Database helper functions
const db = {
  // Subjects operations
  async saveSubject(subjectData) {
    const { data, error } = await supabase
      .from('subjects')
      .insert([subjectData]);
    
    if (error) throw error;
    return data;
  },

  async getSubjects(filters = {}) {
    let query = supabase.from('subjects').select('*');
    
    if (filters.department) query = query.eq('department', filters.department);
    if (filters.academic_year) query = query.eq('academic_year', filters.academic_year);
    if (filters.year) query = query.eq('year', filters.year);
    if (filters.semester) query = query.eq('semester', filters.semester);
    
    const { data, error } = await query;
    if (error) throw error;
    return data;
  },

  async updateSubject(id, updates) {
    const { data, error } = await supabase
      .from('subjects')
      .update(updates)
      .eq('id', id);
    
    if (error) throw error;
    return data;
  },

  async deleteSubject(id) {
    const { data, error } = await supabase
      .from('subjects')
      .delete()
      .eq('id', id);
    
    if (error) throw error;
    return data;
  },

  // Faculty operations
  async saveFaculty(facultyData) {
    const { data, error } = await supabase
      .from('faculty')
      .insert([facultyData]);
    
    if (error) throw error;
    return data;
  },

  async getFaculty(department = null) {
    let query = supabase.from('faculty').select('*');
    if (department) query = query.eq('department', department);
    
    const { data, error } = await query;
    if (error) throw error;
    return data;
  },

  async updateFaculty(id, updates) {
    const { data, error } = await supabase
      .from('faculty')
      .update(updates)
      .eq('id', id);
    
    if (error) throw error;
    return data;
  },

  async deleteFaculty(id) {
    const { data, error } = await supabase
      .from('faculty')
      .delete()
      .eq('id', id);
    
    if (error) throw error;
    return data;
  },

  // User authentication operations
  async signUp(email, password, userData) {
    const { data, error } = await supabase.auth.signUp({
      email: email,
      password: password,
      options: {
        data: userData
      }
    });
    
    if (error) throw error;
    return data;
  },

  async signIn(email, password) {
    const { data, error } = await supabase.auth.signInWithPassword({
      email: email,
      password: password
    });
    
    if (error) throw error;
    return data;
  },

  async signOut() {
    const { error } = await supabase.auth.signOut();
    if (error) throw error;
  },

  async getCurrentUser() {
    const { data: { user } } = await supabase.auth.getUser();
    return user;
  }
};

// Utility functions
function showToast(message, type = 'info') {
  const toast = document.getElementById('toast') || createToast();
  toast.textContent = message;
  toast.className = `toast toast-${type}`;
  toast.style.display = 'block';
  
  setTimeout(() => {
    toast.style.display = 'none';
  }, 3000);
}

function createToast() {
  const toast = document.createElement('div');
  toast.id = 'toast';
  toast.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    padding: 12px 20px;
    border-radius: 6px;
    color: white;
    font-weight: 500;
    z-index: 10000;
    display: none;
  `;
  document.body.appendChild(toast);
  return toast;
}