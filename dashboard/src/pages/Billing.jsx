import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

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

  if (loading) return <div className="animate-pulse space-y-4"><div className="h-8 w-48 bg-muted rounded"></div><div className="grid gap-4 md:grid-cols-2"><div className="h-32 bg-muted rounded"></div><div className="h-32 bg-muted rounded"></div></div></div>;
  if (!data) return <div className="text-destructive">Failed to load billing</div>;

  const usagePercent = Math.min(100, (data.current_cycle_requests / data.plan_limit_requests) * 100);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Billing & Usage</h1>
        <p className="text-muted-foreground mt-2">Manage your subscription and view current usage.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Current Cost</CardTitle>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" className="h-4 w-4 text-muted-foreground"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${data.current_cycle_cost_usd.toFixed(2)}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">API Requests</CardTitle>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" className="h-4 w-4 text-muted-foreground"><path d="M22 12h-4l-3 9L9 3l-3 9H2"></path></svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {data.current_cycle_requests.toLocaleString()} 
              <span className="text-sm text-muted-foreground font-normal ml-1">/ {data.plan_limit_requests.toLocaleString()}</span>
            </div>
            <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-secondary">
              <div 
                className={`h-full ${usagePercent > 90 ? 'bg-destructive' : 'bg-primary'}`} 
                style={{ width: `${usagePercent}%` }}
              />
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Current Plan</CardTitle>
          <CardDescription>You are currently on the Pro Tier ($0.05 / request).</CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={() => alert('Manage subscription coming soon')}>
            Manage Subscription
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
