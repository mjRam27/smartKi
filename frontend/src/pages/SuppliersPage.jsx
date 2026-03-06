import React, { useState, useEffect } from 'react';
import { Header } from '../components/layout';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { suppliersAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { Plus, Search, Truck, Loader2, Edit, Star, Phone, Mail, Globe } from 'lucide-react';

export const SuppliersPage = () => {
  const { hasRole } = useAuth();
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showDialog, setShowDialog] = useState(false);
  const [editingSupplier, setEditingSupplier] = useState(null);
  const [formData, setFormData] = useState({
    name: '', contact_name: '', email: '', phone: '', address: '', city: '', country: '',
    payment_terms: '', lead_time_days: '', minimum_order_value: '', categories: '',
  });

  const fetchSuppliers = async () => {
    setLoading(true);
    try {
      const params = search ? { search } : {};
      const response = await suppliersAPI.list(params);
      setSuppliers(response.data);
    } catch (err) {
      console.error('Failed to fetch:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(fetchSuppliers, 300);
    return () => clearTimeout(timer);
  }, [search]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        lead_time_days: formData.lead_time_days ? parseInt(formData.lead_time_days) : null,
        minimum_order_value: formData.minimum_order_value ? parseFloat(formData.minimum_order_value) : null,
        categories: formData.categories ? formData.categories.split(',').map(s => s.trim()) : [],
      };
      if (editingSupplier) {
        await suppliersAPI.update(editingSupplier.id, payload);
      } else {
        await suppliersAPI.create(payload);
      }
      setShowDialog(false);
      resetForm();
      fetchSuppliers();
    } catch (err) {
      console.error('Failed to save:', err);
    }
  };

  const handleEdit = (sup) => {
    setEditingSupplier(sup);
    setFormData({
      name: sup.name, contact_name: sup.contact_name || '', email: sup.email || '',
      phone: sup.phone || '', address: sup.address || '', city: sup.city || '',
      country: sup.country || '', payment_terms: sup.payment_terms || '',
      lead_time_days: sup.lead_time_days?.toString() || '',
      minimum_order_value: sup.minimum_order_value?.toString() || '',
      categories: sup.categories?.join(', ') || '',
    });
    setShowDialog(true);
  };

  const resetForm = () => {
    setEditingSupplier(null);
    setFormData({ name: '', contact_name: '', email: '', phone: '', address: '', city: '', country: '', payment_terms: '', lead_time_days: '', minimum_order_value: '', categories: '' });
  };

  const renderRating = (rating) => {
    if (!rating) return <span className="text-muted-foreground">-</span>;
    return (
      <div className="flex items-center gap-1">
        {[1, 2, 3, 4, 5].map(i => (
          <Star key={i} className={`h-3 w-3 ${i <= rating ? 'fill-amber-500 text-amber-500' : 'text-muted-foreground'}`} />
        ))}
      </div>
    );
  };

  return (
    <div className="flex min-h-screen flex-col" data-testid="suppliers-page">
      <Header title="Suppliers" subtitle="Manage your supplier network" />
      <div className="flex-1 space-y-6 p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="relative max-w-sm flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input placeholder="Search suppliers..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" />
          </div>
          {hasRole(['admin', 'kitchen_manager', 'procurement_manager']) && (
            <Button onClick={() => { resetForm(); setShowDialog(true); }}>
              <Plus className="mr-2 h-4 w-4" />New Supplier
            </Button>
          )}
        </div>
        <Card>
          <CardContent className="p-0">
            {loading ? (
              <div className="flex h-64 items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-primary" /></div>
            ) : suppliers.length === 0 ? (
              <div className="flex h-64 flex-col items-center justify-center text-muted-foreground">
                <Truck className="mb-4 h-12 w-12" /><p>No suppliers found</p>
              </div>
            ) : (
              <Table className="data-table">
                <TableHeader>
                  <TableRow>
                    <TableHead>Supplier</TableHead><TableHead>Contact</TableHead><TableHead>Location</TableHead>
                    <TableHead>Lead Time</TableHead><TableHead>Min Order</TableHead><TableHead>Rating</TableHead>
                    <TableHead>Status</TableHead><TableHead className="w-12"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {suppliers.map((sup) => (
                    <TableRow key={sup.id}>
                      <TableCell>
                        <div>
                          <span className="font-medium">{sup.name}</span>
                          {sup.categories?.length > 0 && (
                            <div className="mt-1 flex flex-wrap gap-1">
                              {sup.categories.slice(0, 2).map(cat => (
                                <Badge key={cat} variant="outline" className="text-xs">{cat}</Badge>
                              ))}
                            </div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="space-y-1 text-sm">
                          {sup.contact_name && <p>{sup.contact_name}</p>}
                          {sup.email && <p className="flex items-center gap-1 text-muted-foreground"><Mail className="h-3 w-3" />{sup.email}</p>}
                          {sup.phone && <p className="flex items-center gap-1 text-muted-foreground"><Phone className="h-3 w-3" />{sup.phone}</p>}
                        </div>
                      </TableCell>
                      <TableCell>{sup.city ? `${sup.city}${sup.country ? ', ' + sup.country : ''}` : '-'}</TableCell>
                      <TableCell className="font-mono">{sup.lead_time_days ? `${sup.lead_time_days}d` : '-'}</TableCell>
                      <TableCell className="font-mono">{sup.minimum_order_value ? `$${sup.minimum_order_value}` : '-'}</TableCell>
                      <TableCell>{renderRating(sup.rating)}</TableCell>
                      <TableCell>
                        <Badge className={sup.status === 'active' ? 'badge-success' : 'badge-warning'}>{sup.status}</Badge>
                      </TableCell>
                      <TableCell>
                        <Button variant="ghost" size="icon" onClick={() => handleEdit(sup)}><Edit className="h-4 w-4" /></Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader><DialogTitle>{editingSupplier ? 'Edit Supplier' : 'New Supplier'}</DialogTitle></DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label className="form-label">Name *</Label>
              <Input value={formData.name} onChange={(e) => setFormData(p => ({...p, name: e.target.value}))} required />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="form-label">Contact Name</Label>
                <Input value={formData.contact_name} onChange={(e) => setFormData(p => ({...p, contact_name: e.target.value}))} />
              </div>
              <div className="space-y-2">
                <Label className="form-label">Email</Label>
                <Input type="email" value={formData.email} onChange={(e) => setFormData(p => ({...p, email: e.target.value}))} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="form-label">Phone</Label>
                <Input value={formData.phone} onChange={(e) => setFormData(p => ({...p, phone: e.target.value}))} />
              </div>
              <div className="space-y-2">
                <Label className="form-label">City</Label>
                <Input value={formData.city} onChange={(e) => setFormData(p => ({...p, city: e.target.value}))} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="form-label">Lead Time (days)</Label>
                <Input type="number" value={formData.lead_time_days} onChange={(e) => setFormData(p => ({...p, lead_time_days: e.target.value}))} />
              </div>
              <div className="space-y-2">
                <Label className="form-label">Min Order Value ($)</Label>
                <Input type="number" step="0.01" value={formData.minimum_order_value} onChange={(e) => setFormData(p => ({...p, minimum_order_value: e.target.value}))} />
              </div>
            </div>
            <div className="space-y-2">
              <Label className="form-label">Categories (comma separated)</Label>
              <Input value={formData.categories} onChange={(e) => setFormData(p => ({...p, categories: e.target.value}))} placeholder="produce, meat, dairy" />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowDialog(false)}>Cancel</Button>
              <Button type="submit">{editingSupplier ? 'Update' : 'Create'}</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default SuppliersPage;
