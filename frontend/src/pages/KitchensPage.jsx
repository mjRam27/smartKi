import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Header } from '../components/layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { kitchensAPI, organizationsAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { useApp } from '../contexts/AppContext';
import { Plus, Building2, Loader2, Edit, MapPin, Users } from 'lucide-react';

export const KitchensPage = () => {
  const navigate = useNavigate();
  const { user, hasRole } = useAuth();
  const { refreshKitchens, organization, setOrganization } = useApp();
  const [kitchens, setKitchens] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showKitchenDialog, setShowKitchenDialog] = useState(false);
  const [showOrgDialog, setShowOrgDialog] = useState(false);
  const [editingKitchen, setEditingKitchen] = useState(null);
  const [kitchenForm, setKitchenForm] = useState({ name: '', location: '', description: '', capacity: '' });
  const [orgForm, setOrgForm] = useState({ name: '', type: 'other', description: '', address: '', phone: '', email: '' });

  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await kitchensAPI.list();
      setKitchens(response.data);
    } catch (err) {
      console.error('Failed to fetch:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const handleKitchenSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...kitchenForm,
        capacity: kitchenForm.capacity ? parseInt(kitchenForm.capacity) : null,
      };
      if (editingKitchen) {
        await kitchensAPI.update(editingKitchen.id, payload);
      } else {
        await kitchensAPI.create(payload);
      }
      setShowKitchenDialog(false);
      setKitchenForm({ name: '', location: '', description: '', capacity: '' });
      setEditingKitchen(null);
      fetchData();
      refreshKitchens();
    } catch (err) {
      console.error('Failed to save:', err);
    }
  };

  const handleOrgSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await organizationsAPI.create(orgForm);
      setOrganization(response.data);
      setShowOrgDialog(false);
    } catch (err) {
      console.error('Failed to create org:', err);
    }
  };

  const handleEditKitchen = (kitchen) => {
    setEditingKitchen(kitchen);
    setKitchenForm({
      name: kitchen.name, location: kitchen.location || '',
      description: kitchen.description || '', capacity: kitchen.capacity?.toString() || '',
    });
    setShowKitchenDialog(true);
  };

  // If no organization, prompt to create one
  if (!organization && !user?.organization_id) {
    return (
      <div className="flex min-h-screen flex-col" data-testid="kitchens-page">
        <Header title="Organization Setup" subtitle="Create your organization first" />
        <div className="flex flex-1 items-center justify-center p-6">
          <Card className="max-w-md">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Building2 className="h-5 w-5" />
                Create Organization
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="mb-4 text-sm text-muted-foreground">
                You need to create an organization before adding kitchens.
              </p>
              <Button onClick={() => setShowOrgDialog(true)} className="w-full">
                <Plus className="mr-2 h-4 w-4" />Create Organization
              </Button>
            </CardContent>
          </Card>
        </div>
        <Dialog open={showOrgDialog} onOpenChange={setShowOrgDialog}>
          <DialogContent>
            <DialogHeader><DialogTitle>Create Organization</DialogTitle></DialogHeader>
            <form onSubmit={handleOrgSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label className="form-label">Organization Name *</Label>
                <Input value={orgForm.name} onChange={(e) => setOrgForm(p => ({...p, name: e.target.value}))} required placeholder="Acme Food Services" />
              </div>
              <div className="space-y-2">
                <Label className="form-label">Type</Label>
                <Select value={orgForm.type} onValueChange={(v) => setOrgForm(p => ({...p, type: v}))}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="corporate_cafeteria">Corporate Cafeteria</SelectItem>
                    <SelectItem value="hospital">Hospital</SelectItem>
                    <SelectItem value="university">University</SelectItem>
                    <SelectItem value="catering">Catering</SelectItem>
                    <SelectItem value="restaurant">Restaurant</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label className="form-label">Address</Label>
                <Input value={orgForm.address} onChange={(e) => setOrgForm(p => ({...p, address: e.target.value}))} />
              </div>
              <DialogFooter>
                <Button type="submit">Create Organization</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col" data-testid="kitchens-page">
      <Header title="Kitchens" subtitle={organization?.name} />
      <div className="flex-1 space-y-6 p-6">
        {/* Organization Info */}
        {organization && (
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="flex h-12 w-12 items-center justify-center rounded-sm bg-primary/10">
                    <Building2 className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-semibold">{organization.name}</h3>
                    <p className="text-sm text-muted-foreground capitalize">{organization.type?.replace('_', ' ')}</p>
                  </div>
                </div>
                <Badge className="badge-success">{organization.subscription_tier}</Badge>
              </div>
            </CardContent>
          </Card>
        )}

        <div className="flex justify-between">
          <h2 className="text-lg font-semibold">Kitchens ({kitchens.length})</h2>
          {hasRole(['admin', 'kitchen_manager']) && (
            <Button onClick={() => { setEditingKitchen(null); setKitchenForm({ name: '', location: '', description: '', capacity: '' }); setShowKitchenDialog(true); }}>
              <Plus className="mr-2 h-4 w-4" />Add Kitchen
            </Button>
          )}
        </div>

        {loading ? (
          <div className="flex h-64 items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-primary" /></div>
        ) : kitchens.length === 0 ? (
          <Card>
            <CardContent className="flex h-64 flex-col items-center justify-center text-muted-foreground">
              <Building2 className="mb-4 h-12 w-12" />
              <p>No kitchens yet. Add your first kitchen to get started.</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {kitchens.map((kitchen) => (
              <Card key={kitchen.id} className="card-interactive">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-semibold">{kitchen.name}</h3>
                      {kitchen.location && (
                        <p className="mt-1 flex items-center gap-1 text-sm text-muted-foreground">
                          <MapPin className="h-3 w-3" />{kitchen.location}
                        </p>
                      )}
                      {kitchen.capacity && (
                        <p className="mt-1 flex items-center gap-1 text-sm text-muted-foreground">
                          <Users className="h-3 w-3" />Capacity: {kitchen.capacity}
                        </p>
                      )}
                    </div>
                    <Button variant="ghost" size="icon" onClick={() => handleEditKitchen(kitchen)}>
                      <Edit className="h-4 w-4" />
                    </Button>
                  </div>
                  {kitchen.description && (
                    <p className="mt-2 text-sm text-muted-foreground line-clamp-2">{kitchen.description}</p>
                  )}
                  <Badge className={kitchen.is_active ? 'badge-success' : 'badge-error'} style={{ marginTop: '8px' }}>
                    {kitchen.is_active ? 'Active' : 'Inactive'}
                  </Badge>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      <Dialog open={showKitchenDialog} onOpenChange={setShowKitchenDialog}>
        <DialogContent>
          <DialogHeader><DialogTitle>{editingKitchen ? 'Edit Kitchen' : 'Add Kitchen'}</DialogTitle></DialogHeader>
          <form onSubmit={handleKitchenSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label className="form-label">Kitchen Name *</Label>
              <Input value={kitchenForm.name} onChange={(e) => setKitchenForm(p => ({...p, name: e.target.value}))} required placeholder="Main Kitchen" />
            </div>
            <div className="space-y-2">
              <Label className="form-label">Location</Label>
              <Input value={kitchenForm.location} onChange={(e) => setKitchenForm(p => ({...p, location: e.target.value}))} placeholder="Building A, Floor 1" />
            </div>
            <div className="space-y-2">
              <Label className="form-label">Capacity</Label>
              <Input type="number" value={kitchenForm.capacity} onChange={(e) => setKitchenForm(p => ({...p, capacity: e.target.value}))} placeholder="Number of staff" />
            </div>
            <div className="space-y-2">
              <Label className="form-label">Description</Label>
              <Input value={kitchenForm.description} onChange={(e) => setKitchenForm(p => ({...p, description: e.target.value}))} />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowKitchenDialog(false)}>Cancel</Button>
              <Button type="submit">{editingKitchen ? 'Update' : 'Create'}</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default KitchensPage;
