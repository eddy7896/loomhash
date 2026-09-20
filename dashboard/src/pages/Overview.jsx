import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function Overview() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/v1/admin/analytics')
      .then(res => res.json())
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading-pulse">Loading analytics...</div>;
  if (!data) return <div>Failed to load analytics</div>;

  // Transform recent events into a simple timeseries for the chart
  // This is a naive grouping by minute for demonstration
  const chartData = data.recent_events.reduce((acc, event) => {
    const d = new Date(event.created_at * 1000);
    const timeKey = `${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`;
    const existing = acc.find(x => x.time === timeKey);
    if (existing) {
      existing.requests += 1;
    } else {
      acc.push({ time: timeKey, requests: 1 });
    }
    return acc;
  }, []).reverse(); // Reverse to get chronological order

  return (
    <div className="overview-page">
      <h1>Overview</h1>
      <p className="subtitle">Real-time metrics and API usage</p>

      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-title">Total API Requests</div>
          <div className="metric-value">{data.total_requests.toLocaleString()}</div>
        </div>
        <div className="metric-card">
          <div className="metric-title">Success Rate</div>
          <div className="metric-value" style={{color: data.success_rate_percent >= 99 ? 'var(--accent-green)' : 'var(--text-main)'}}>
            {data.success_rate_percent}%
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-title">Failed Requests</div>
          <div className="metric-value">{data.total_failures.toLocaleString()}</div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Recent Traffic</h3>
          <p>Requests over time from your applications</p>
        </div>
        <div className="card-body" style={{ height: '300px' }}>
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-dim)" vertical={false} />
                <XAxis dataKey="time" stroke="var(--text-muted)" tick={{fill: 'var(--text-muted)', fontSize: 12}} />
                <YAxis stroke="var(--text-muted)" tick={{fill: 'var(--text-muted)', fontSize: 12}} />
                <Tooltip 
                  contentStyle={{ backgroundColor: 'var(--bg-surface)', borderColor: 'var(--border-dim)' }}
                  itemStyle={{ color: 'var(--text-main)' }}
                />
                <Line type="monotone" dataKey="requests" stroke="var(--accent-blue)" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
              No recent traffic data
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Recent Events</h3>
          <p>The 50 most recent API calls to the server</p>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Endpoint</th>
              <th>Status</th>
              <th>Latency</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            {data.recent_events.map((event, i) => (
              <tr key={i}>
                <td className="text-mono">{event.endpoint}</td>
                <td>
                  <span className={`badge ${event.status_code === 200 ? 'badge-active' : 'badge-error'}`}>
                    {event.status_code}
                  </span>
                </td>
                <td className="text-mono">{event.latency_ms} ms</td>
                <td>{new Date(event.created_at * 1000).toLocaleTimeString()}</td>
              </tr>
            ))}
            {data.recent_events.length === 0 && (
              <tr>
                <td colSpan="4" style={{textAlign: 'center', color: 'var(--text-muted)'}}>No events logged yet</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
