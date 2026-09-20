import { useState, useEffect } from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

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
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Users</h1>
        <p className="text-muted-foreground mt-2">Data subjects currently enrolled in the system.</p>
      </div>

      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>User ID</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={3} className="text-center h-24 text-muted-foreground animate-pulse">
                  Loading users...
                </TableCell>
              </TableRow>
            ) : !data || data.users.length === 0 ? (
              <TableRow>
                <TableCell colSpan={3} className="text-center h-24 text-muted-foreground">
                  No users enrolled yet.
                </TableCell>
              </TableRow>
            ) : (
              data.users.map((userId) => (
                <TableRow key={userId}>
                  <TableCell className="font-mono font-medium">{userId}</TableCell>
                  <TableCell>
                    <Badge variant="success">Enrolled</Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <Button 
                      variant="outline"
                      size="sm"
                      onClick={() => alert('View user details coming soon.')}
                    >
                      View
                    </Button>
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
