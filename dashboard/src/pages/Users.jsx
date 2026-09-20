import { useState, useEffect } from 'react';

export default function Users() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/v1/admin/users')
      .then(res => res.json())
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="users-page">
      <h1>Users</h1>
      <p className="subtitle">Data subjects currently enrolled in the system.</p>

      <div className="card">
        <table className="data-table">
          <thead>
            <tr>
              <th>User ID</th>
              <th>Status</th>
              <th style={{textAlign: 'right'}}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan="3" className="loading-pulse" style={{textAlign: 'center'}}>Loading users...</td>
              </tr>
            ) : !data || data.users.length === 0 ? (
              <tr>
                <td colSpan="3" style={{textAlign: 'center', color: 'var(--text-muted)'}}>No users enrolled yet.</td>
              </tr>
            ) : (
              data.users.map((userId) => (
                <tr key={userId}>
                  <td className="text-mono">{userId}</td>
                  <td><span className="badge badge-active">Enrolled</span></td>
                  <td style={{textAlign: 'right'}}>
                    <button 
                      className="btn btn-secondary" 
                      onClick={() => alert('View user details coming soon.')}
                    >
                      View
                    </button>
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
