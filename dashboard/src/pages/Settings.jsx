import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

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
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="animate-pulse space-y-4"><div className="h-8 w-48 bg-muted rounded"></div><div className="h-64 w-full bg-muted rounded"></div></div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Project Settings</h1>
        <p className="text-muted-foreground mt-2">Configure your LoomHash environment.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>General Settings</CardTitle>
          <CardDescription>Basic project configuration.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 max-w-sm">
            <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">Project Name</label>
            <Input 
              type="text" 
              name="project_name" 
              value={settings.project_name || ''} 
              onChange={handleChange}
            />
          </div>
        </CardContent>
        <CardFooter className="border-t bg-muted/40 px-6 py-4">
          <Button 
            onClick={() => handleSave('project_name')}
            disabled={saving}
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </Button>
        </CardFooter>
      </Card>
      
      <Card className="border-destructive/50">
        <CardHeader>
          <CardTitle className="text-destructive">Danger Zone</CardTitle>
          <CardDescription>Irreversible and destructive actions.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <h4 className="text-sm font-medium leading-none">Delete Project</h4>
              <p className="text-sm text-muted-foreground">
                Permanently delete this project, all API keys, and all enrolled users.
              </p>
            </div>
            <Button variant="destructive" onClick={() => alert('Cannot delete project in prototype mode.')}>
              Delete Project
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
