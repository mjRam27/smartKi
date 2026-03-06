import React, { useState, useEffect } from 'react';
import { Header } from '../components/layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Badge } from '../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { wasteAPI } from '../services/api';
import { useApp } from '../contexts/AppContext';
import { Plus, Trash2, Loader2, TrendingDown, DollarSign } from 'lucide-react';

const WASTE_REASONS = [
  { value: 'expired', label: 'Expired' },
  { value: 'spoiled', label: 'Spoiled' },
  { value: 'overproduction', label: 'Overproduction' },
  { value: 'plate_waste', label: 'Plate Waste' },
  { value: 'prep_waste', label: 'Prep Waste' },
  { value: 'damaged', label: 'Damaged' },
  { value: 'quality_issue', label: 'Quality Issue' },
  { value: 'other', label: 'Other' },
];

export const WastePage = () => {
  const { selectedKitchen, kitchens } = useApp();
  const [wasteLogs, setWasteLogs] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [formData, setFormData] = useState({
    kitchen_id: '', ingredient_name: '', quantity: '', unit: 'kg',
    reason: 'expired', estimated_cost: '', notes: '',
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      const params = selectedKitchen ? { kitchen_id: selectedKitchen.id } : {};
      const [logsRes, summaryRes] = await Promise.all([
        wasteAPI.list(params),
        wasteAPI.summary(params),
      ]);
      setWasteLogs(logsRes.data);
      setSummary(summaryRes.data);
    } catch (err) {
      console.error('Failed to fetch:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [selectedKitchen]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await wasteAPI.create({
        ...formData,
        kitchen_id: formData.kitchen_id || selectedKitchen?.id,
        quantity: parseFloat(formData.quantity),
        estimated_cost: formData.estimated_cost ? parseFloat(formData.estimated_cost) : null,
      });
      setShowDialog(false);
      setFormData({ kitchen_id: '', ingredient_name: '', quantity: '', unit: 'kg', reason: 'expired', estimated_cost: '', notes: '' });
      fetchData();
    } catch (err) {
      console.error('Failed to log waste:', err);
    }
  };

  const reasonColors = {
    expired: 'badge-error', spoiled: 'badge-error', overproduction: 'badge-warning',
    plate_waste: 'badge-warning', prep_waste: 'badge-info', damaged: 'badge-error',
    quality_issue: 'badge-warning', other: 'badge-info',
  };

  return (
    <div className="flex min-h-screen flex-col" data-testid="waste-page">
      <Header title="Waste Log" subtitle="Track and analyze food waste" />
      <div className="flex-1 space-y-6 p-6">
        {/* Summary Cards */}
        <div className="grid gap-4 sm:grid-cols-3">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs uppercase tracking-wider text-muted-foreground">Total Entries</p>
                  <p className="mt-1 font-mono text-2xl font-semibold">{summary?.total_entries || 0}</p>
                </div>
                <Trash2 className="h-8 w-8 text-muted-foreground" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs uppercase tracking-wider text-muted-foreground">Total Cost</p>
                  <p className="mt-1 font-mono text-2xl font-semibold text-red-500">${summary?.total_cost?.toFixed(2) || '0.00'}</p>
                </div>
                <DollarSign className="h-8 w-8 text-red-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs uppercase tracking-wider text-muted-foreground">Top Reason</p>
                  <p className="mt-1 text-lg font-semibold capitalize">
                    {summary?.by_reason ? Object.entries(summary.by_reason).sort((a, b) => b[1].count - a[1].count)[0]?.[0]?.replace('_', ' ') || '-' : '-'}
                  </p>
                </div>
                <TrendingDown className="h-8 w-8 text-amber-500" />
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="flex justify-end">
          <Button onClick={() => setShowDialog(true)} data-testid="log-waste-btn">
            <Plus className="mr-2 h-4 w-4" />Log Waste
          </Button>
        </div>

        <Card>
          <CardContent className="p-0">
            {loading ? (
              <div className="flex h-64 items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-primary" /></div>
            ) : wasteLogs.length === 0 ? (
              <div className="flex h-64 flex-col items-center justify-center text-muted-foreground">
                <Trash2 className="mb-4 h-12 w-12" /><p>No waste logged yet</p>
              </div>
            ) : (
              <Table className="data-table">
                <TableHeader>
                  <TableRow>
                    <TableHead>Item</TableHead><TableHead>Quantity</TableHead><TableHead>Reason</TableHead>
                    <TableHead>Cost</TableHead><TableHead>Date</TableHead><TableHead>Notes</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {wasteLogs.map((log) => (
                    <TableRow key={log.id}>
                      <TableCell className="font-medium">{log.ingredient_name || log.recipe_name}</TableCell>
                      <TableCell className="font-mono">{log.quantity} {log.unit}</TableCell>
                      <TableCell>
                        <Badge className={reasonColors[log.reason] || 'badge-info'}>{log.reason.replace('_', ' ')}</Badge>
                      </TableCell>
                      <TableCell className="font-mono">{log.estimated_cost ? `$${log.estimated_cost.toFixed(2)}` : '-'}</TableCell>
                      <TableCell className="font-mono text-muted-foreground">
                        {new Date(log.logged_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="max-w-xs truncate text-muted-foreground">{log.notes || '-'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>

      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent>
          <DialogHeader><DialogTitle>Log Waste</DialogTitle></DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            {kitchens.length > 1 && (
              <div className="space-y-2">
                <Label className="form-label">Kitchen</Label>
                <Select value={formData.kitchen_id || selectedKitchen?.id || ''} onValueChange={(v) => setFormData(p => ({...p, kitchen_id: v}))}>
                  <SelectTrigger><SelectValue placeholder="Select kitchen" /></SelectTrigger>
                  <SelectContent>{kitchens.map(k => <SelectItem key={k.id} value={k.id}>{k.name}</SelectItem>)}</SelectContent>
                </Select>
              </div>
            )}
            <div className="space-y-2">
              <Label className="form-label">Item Name *</Label>
              <Input value={formData.ingredient_name} onChange={(e) => setFormData(p => ({...p, ingredient_name: e.target.value}))} required placeholder="Ingredient or recipe name" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="form-label">Quantity *</Label>
                <Input type="number" step="0.01" value={formData.quantity} onChange={(e) => setFormData(p => ({...p, quantity: e.target.value}))} required />
              </div>
              <div className="space-y-2">
                <Label className="form-label">Unit</Label>
                <Input value={formData.unit} onChange={(e) => setFormData(p => ({...p, unit: e.target.value}))} placeholder="kg, L, servings" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="form-label">Reason *</Label>
                <Select value={formData.reason} onValueChange={(v) => setFormData(p => ({...p, reason: v}))}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>{WASTE_REASONS.map(r => <SelectItem key={r.value} value={r.value}>{r.label}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label className="form-label">Est. Cost ($)</Label>
                <Input type="number" step="0.01" value={formData.estimated_cost} onChange={(e) => setFormData(p => ({...p, estimated_cost: e.target.value}))} />
              </div>
            </div>
            <div className="space-y-2">
              <Label className="form-label">Notes</Label>
              <Textarea value={formData.notes} onChange={(e) => setFormData(p => ({...p, notes: e.target.value}))} rows={2} />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowDialog(false)}>Cancel</Button>
              <Button type="submit">Log Waste</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default WastePage;
