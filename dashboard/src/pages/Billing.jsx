import { useState, useEffect } from 'react';

export default function Billing() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/v1/admin/billing')
      .then(res => res.json())
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading-pulse">Loading billing...</div>;
  if (!data) return <div>Failed to load billing</div>;

  const usagePercent = Math.min(100, (data.current_cycle_requests / data.plan_limit_requests) * 100);

  return (
    <div className="billing-page">
      <h1>Billing & Usage</h1>
      <p className="subtitle">Manage your subscription and view current usage.</p>

      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-title">Current Cost</div>
          <div className="metric-value">${data.current_cycle_cost_usd.toFixed(2)}</div>
        </div>
        <div className="metric-card">
          <div className="metric-title">API Requests</div>
          <div className="metric-value">{data.current_cycle_requests.toLocaleString()} <span style={{fontSize: '1rem', color: 'var(--text-muted)'}}>/ {data.plan_limit_requests.toLocaleString()}</span></div>
          <div style={{ marginTop: '12px', height: '4px', backgroundColor: 'var(--border-dim)', borderRadius: '2px', overflow: 'hidden' }}>
            <div style={{ height: '100%', width: `${usagePercent}%`, backgroundColor: usagePercent > 90 ? 'var(--accent-red)' : 'var(--accent-blue)' }} />
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Current Plan</h3>
          <p>You are currently on the Pro Tier ($0.05 / request).</p>
        </div>
        <div className="card-body">
          <button className="btn btn-primary" onClick={() => alert('Manage subscription coming soon')}>Manage Subscription</button>
        </div>
      </div>
    </div>
  );
}
