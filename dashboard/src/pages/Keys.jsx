import { useState, useEffect } from 'react';

export default function Keys() {
  const [keys, setKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newKey, setNewKey] = useState(null);

  const fetchKeys = () => {
    setLoading(true);
    fetch('/v1/admin/keys')
      .then(res => res.json())
      .then(setKeys)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchKeys();
  }, []);

  const handleGenerate = async () => {
    try {
      const res = await fetch('/v1/admin/keys', { method: 'POST' });
      const data = await res.json();
      setNewKey(data.raw_key);
      fetchKeys(); // Refresh list
    } catch (err) {
      console.error(err);
    }
  };

  const handleRevoke = async (key_id) => {
    if (!confirm('Are you sure you want to revoke this API key? This action cannot be undone and integrations using it will immediately fail.')) return;
    
    try {
      await fetch(`/v1/admin/keys/${key_id}`, { method: 'DELETE' });
      fetchKeys();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="keys-page">
      <div className="flex-between">
        <div>
          <h1>Authentication</h1>
          <p className="subtitle">Manage API keys to authenticate your server requests.</p>
        </div>
        <button className="btn btn-primary" onClick={handleGenerate}>Generate New Key</button>
      </div>

      {newKey && (
        <div className="card" style={{ borderColor: 'var(--accent-blue)', backgroundColor: 'rgba(59, 130, 246, 0.05)' }}>
          <div className="card-body">
            <h3 style={{ color: 'var(--accent-blue)', marginBottom: '12px' }}>Save your new API key!</h3>
            <p style={{ color: 'var(--text-muted)', marginBottom: '16px' }}>
              For your security, this is the only time we will show you the full API key secret. Please copy it now.
            </p>
            <div style={{ display: 'flex', gap: '12px' }}>
              <input type="text" className="form-input text-mono" value={newKey} readOnly />
              <button 
                className="btn btn-secondary" 
                onClick={() => {
                  navigator.clipboard.writeText(newKey);
                  alert('Copied to clipboard!');
                }}
              >
                Copy
              </button>
            </div>
            <button 
              className="btn" 
              style={{ marginTop: '16px', color: 'var(--text-muted)' }}
              onClick={() => setNewKey(null)}
            >
              I have saved it securely
            </button>
          </div>
        </div>
      )}

      <div className="card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Key ID</th>
              <th>Created</th>
              <th>Status</th>
              <th style={{textAlign: 'right'}}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan="4" className="loading-pulse" style={{textAlign: 'center'}}>Loading keys...</td>
              </tr>
            ) : keys.length === 0 ? (
              <tr>
                <td colSpan="4" style={{textAlign: 'center', color: 'var(--text-muted)'}}>No API keys generated yet.</td>
              </tr>
            ) : (
              keys.map((k) => (
                <tr key={k.key_id}>
                  <td className="text-mono">{k.key_id}</td>
                  <td>{new Date(k.created_at * 1000).toLocaleString()}</td>
                  <td>
                    {k.is_active ? (
                      <span className="badge badge-active">Active</span>
                    ) : (
                      <span className="badge badge-inactive">Revoked</span>
                    )}
                  </td>
                  <td style={{textAlign: 'right'}}>
                    {k.is_active && (
                      <button 
                        className="btn btn-danger" 
                        onClick={() => handleRevoke(k.key_id)}
                      >
                        Revoke
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
