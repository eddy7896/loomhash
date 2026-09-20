import { useState, useEffect } from 'react';

export default function Settings() {
  const [settings, setSettings] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const fetchSettings = () => {
    setLoading(true);
    fetch('/v1/admin/settings')
      .then(res => res.json())
      .then(setSettings)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handleChange = (e) => {
    setSettings(prev => ({...prev, [e.target.name]: e.target.value}));
  };

  const handleSave = async (key) => {
    setSaving(true);
    try {
      await fetch(`/v1/admin/settings/${key}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: settings[key] })
      });
      // Could show a toast notification here
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="loading-pulse">Loading settings...</div>;

  return (
    <div className="settings-page">
      <h1>Project Settings</h1>
      <p className="subtitle">Configure your LoomHash environment.</p>

      <div className="card">
        <div className="card-header">
          <h3>General Settings</h3>
          <p>Basic project configuration.</p>
        </div>
        <div className="card-body">
          <div className="form-group" style={{maxWidth: '400px'}}>
            <label className="form-label">Project Name</label>
            <input 
              type="text" 
              name="project_name" 
              className="form-input" 
              value={settings.project_name || ''} 
              onChange={handleChange}
            />
          </div>
        </div>
        <div className="card-footer">
          <button 
            className="btn btn-primary" 
            onClick={() => handleSave('project_name')}
            disabled={saving}
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>
      
      <div className="card" style={{ borderColor: 'var(--border-dim)' }}>
        <div className="card-header">
          <h3 style={{ color: 'var(--accent-red)' }}>Danger Zone</h3>
          <p>Irreversible and destructive actions.</p>
        </div>
        <div className="card-body">
          <div className="flex-between">
            <div>
              <h4 style={{marginBottom: '4px', fontWeight: 500}}>Delete Project</h4>
              <p style={{color: 'var(--text-muted)', fontSize: '0.9rem'}}>
                Permanently delete this project, all API keys, and all enrolled users.
              </p>
            </div>
            <button className="btn btn-danger" onClick={() => alert('Cannot delete project in prototype mode.')}>
              Delete Project
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
