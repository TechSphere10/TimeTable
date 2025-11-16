// Supabase configuration
const SUPABASE_URL = 'https://bkmzyhroignpjebfpqug.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJrbXp5aHJvaWducGplYmZwcXVnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc0MjA1NDUsImV4cCI6MjA3Mjk5NjU0NX0.ICE2eYzFZvz0dtNpAa5YlJTZD-idc2J76wn1ZeHwwck';

// Backend server URL (for potential future use, currently using JS GA)
const BACKEND_URL = 'http://127.0.0.1:5000';

if (typeof window.supabase === 'undefined') {
    alert("Supabase client library not found. Please check the script tag.");
}
const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);