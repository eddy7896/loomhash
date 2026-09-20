import { useState, useEffect } from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';

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
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Authentication</h1>
          <p className="text-muted-foreground mt-2">Manage API keys to authenticate your server requests.</p>
        </div>
        <Button onClick={handleGenerate}>Generate New Key</Button>
      </div>

      {newKey && (
        <Card className="border-primary bg-primary/5">
          <CardContent className="pt-6">
            <h3 className="text-lg font-medium text-primary mb-2">Save your new API key!</h3>
            <p className="text-sm text-muted-foreground mb-4">
              For your security, this is the only time we will show you the full API key secret. Please copy it now.
            </p>
            <div className="flex gap-3 mb-4">
              <Input type="text" className="font-mono bg-background" value={newKey} readOnly />
              <Button 
                variant="secondary"
                onClick={() => {
                  navigator.clipboard.writeText(newKey);
                  alert('Copied to clipboard!');
                }}
              >
                Copy
              </Button>
            </div>
            <Button 
              variant="ghost" 
              className="text-muted-foreground"
              onClick={() => setNewKey(null)}
            >
              I have saved it securely
            </Button>
          </CardContent>
        </Card>
      )}

      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Key ID</TableHead>
              <TableHead>Created</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={4} className="text-center h-24 text-muted-foreground animate-pulse">Loading keys...</TableCell>
              </TableRow>
            ) : keys.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="text-center h-24 text-muted-foreground">No API keys generated yet.</TableCell>
              </TableRow>
            ) : (
              keys.map((k) => (
                <TableRow key={k.key_id}>
                  <TableCell className="font-mono">{k.key_id}</TableCell>
                  <TableCell>{new Date(k.created_at * 1000).toLocaleString()}</TableCell>
                  <TableCell>
                    {k.is_active ? (
                      <Badge variant="success">Active</Badge>
                    ) : (
                      <Badge variant="secondary">Revoked</Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    {k.is_active && (
                      <Button 
                        variant="destructive"
                        size="sm"
                        onClick={() => handleRevoke(k.key_id)}
                      >
                        Revoke
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}
