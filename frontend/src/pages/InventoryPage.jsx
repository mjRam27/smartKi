import React, { useState, useEffect } from 'react';
import { Header } from '../components/layout';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { inventoryAPI, ingredientsAPI, kitchensAPI } from '../services/api';
import { useApp } from '../contexts/AppContext';
import { Plus, Search, Warehouse, Loader2, AlertTriangle, ArrowUp, ArrowDown, RefreshCw } from 'lucide-react';

export const InventoryPage = () => {
  const { selectedKitchen, kitchens } = useApp();
  const [inventory, setInventory] = useState([]);
  const [ingredients, setIngredients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showDialog, setShowDialog] = useState(false);
  const [showAdjustDialog, setShowAdjustDialog] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [formData, setFormData] = useState({
    ingredient_id: '', kitchen_id: '', quantity: '', unit: 'kg',
    par_level: '', reorder_point: '', cost_per_unit: '', expiry_date: '',
  });
  const [adjustData, setAdjustData] = useState({ quantity: '', movement_type: 'receipt', notes: '' });

  const fetchData = async () => {
    setLoading(true);
    try {
      const params = selectedKitchen ? { kitchen_id: selectedKitchen.id } : {};
      const [invRes, ingRes] = await Promise.all([
        inventoryAPI.list(params),
        ingredientsAPI.list({ limit: 500 })
      ]);
      setInventory(invRes.data);
      setIngredients(ingRes.data);
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
      await inventoryAPI.create({
        ...formData,
        quantity: parseFloat(formData.quantity),
        par_level: formData.par_level ? parseFloat(formData.par_level) : null,
        reorder_point: formData.reorder_point ? parseFloat(formData.reorder_point) : null,
        cost_per_unit: formData.cost_per_unit ? parseFloat(formData.cost_per_unit) : null,
      });
      setShowDialog(false);
      fetchData();
    } catch (err) {
      console.error('Failed to create:', err);
    }
  };

  const handleAdjust = async (e) => {
    e.preventDefault();
    try {
      await inventoryAPI.adjust(selectedItem.id, {
        quantity: parseFloat(adjustData.quantity),
        movement_type: adjustData.movement_type,
        notes: adjustData.notes || undefined,
      });
      setShowAdjustDialog(false);
      fetchData();
    } catch (err) {
      console.error('Failed to adjust:', err);
    }
  };

  const openAdjust = (item, type) => {
    setSelectedItem(item);
    setAdjustData({ quantity: '', movement_type: type, notes: '' });
    setShowAdjustDialog(true);
  };

  const filteredInventory = inventory.filter(item => 
    !search || item.ingredient_name?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="flex min-h-screen flex-col" data-testid="inventory-page">
      <Header title="Inventory" subtitle={selectedKitchen?.name || 'All Kitchens'} />
      <div className="flex-1 space-y-6 p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="relative max-w-sm flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input placeholder="Search inventory..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" />
          </div>
          <Button onClick={() => { setFormData({ ingredient_id: '', kitchen_id: selectedKitchen?.id || '', quantity: '', unit: 'kg', par_level: '', reorder_point: '', cost_per_unit: '', expiry_date: '' }); setShowDialog(true); }}>
            <Plus className="mr-2 h-4 w-4" />Add Item
          </Button>
        </div>
        <Card>
          <CardContent className="p-0">
            {loading ? (
              <div className="flex h-64 items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-primary" /></div>
            ) : filteredInventory.length === 0 ? (
              <div className="flex h-64 flex-col items-center justify-center text-muted-foreground">
                <Warehouse className="mb-4 h-12 w-12" /><p>No inventory items</p>
              </div>
            ) : (
              <Table className="data-table">
                <TableHeader>
                  <TableRow>
                    <TableHead>Item</TableHead><TableHead>Quantity</TableHead><TableHead>Par Level</TableHead>
                    <TableHead>Value</TableHead><TableHead>Expiry</TableHead><TableHead>Status</TableHead><TableHead className="w-32"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredInventory.map((item) => {
                    const isLow = item.reorder_point && item.quantity <= item.reorder_point;
                    const isExpired = item.expiry_date && new Date(item.expiry_date) < new Date();
                    return (
                      <TableRow key={item.id}>
                        <TableCell><span className="font-medium">{item.ingredient_name || 'Unknown'}</span></TableCell>
                        <TableCell className="font-mono">{item.quantity} {item.unit}</TableCell>
                        <TableCell className="font-mono text-muted-foreground">{item.par_level || '-'}</TableCell>
                        <TableCell className="font-mono">{item.total_value ? `$${item.total_value.toFixed(2)}` : '-'}</TableCell>
                        <TableCell className="font-mono">{item.expiry_date || '-'}</TableCell>
                        <TableCell>
                          {isLow && <Badge className="badge-warning"><AlertTriangle className="mr-1 h-3 w-3" />Low</Badge>}
                          {isExpired && <Badge className="badge-error">Expired</Badge>}
                          {!isLow && !isExpired && <Badge className="badge-success">OK</Badge>}
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-1">
                            <Button variant="ghost" size="icon" onClick={() => openAdjust(item, 'receipt')} title="Add Stock">
                              <ArrowUp className="h-4 w-4 text-emerald-500" />
                            </Button>
                            <Button variant="ghost" size="icon" onClick={() => openAdjust(item, 'issue')} title="Remove Stock">
                              <ArrowDown className="h-4 w-4 text-red-500" />
                            </Button>
                            <Button variant="ghost" size="icon" onClick={() => openAdjust(item, 'adjustment')} title="Adjust">
                              <RefreshCw className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
      {/* Add Item Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent>
          <DialogHeader><DialogTitle>Add Inventory Item</DialogTitle></DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label className="form-label">Ingredient *</Label>
              <Select value={formData.ingredient_id} onValueChange={(v) => setFormData(p => ({...p, ingredient_id: v}))}>
                <SelectTrigger><SelectValue placeholder="Select ingredient" /></SelectTrigger>
                <SelectContent>{ingredients.map(ing => <SelectItem key={ing.id} value={ing.id}>{ing.name}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            {kitchens.length > 1 && (
              <div className="space-y-2">
                <Label className="form-label">Kitchen *</Label>
                <Select value={formData.kitchen_id} onValueChange={(v) => setFormData(p => ({...p, kitchen_id: v}))}>
                  <SelectTrigger><SelectValue placeholder="Select kitchen" /></SelectTrigger>
                  <SelectContent>{kitchens.map(k => <SelectItem key={k.id} value={k.id}>{k.name}</SelectItem>)}</SelectContent>
                </Select>
              </div>
            )}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="form-label">Quantity *</Label>
                <Input type="number" step="0.01" value={formData.quantity} onChange={(e) => setFormData(p => ({...p, quantity: e.target.value}))} required />
              </div>
              <div className="space-y-2">
                <Label className="form-label">Unit</Label>
                <Input value={formData.unit} onChange={(e) => setFormData(p => ({...p, unit: e.target.value}))} placeholder="kg, L, unit" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="form-label">Par Level</Label>
                <Input type="number" step="0.01" value={formData.par_level} onChange={(e) => setFormData(p => ({...p, par_level: e.target.value}))} />
              </div>
              <div className="space-y-2">
                <Label className="form-label">Reorder Point</Label>
                <Input type="number" step="0.01" value={formData.reorder_point} onChange={(e) => setFormData(p => ({...p, reorder_point: e.target.value}))} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="form-label">Cost per Unit ($)</Label>
                <Input type="number" step="0.01" value={formData.cost_per_unit} onChange={(e) => setFormData(p => ({...p, cost_per_unit: e.target.value}))} />
              </div>
              <div className="space-y-2">
                <Label className="form-label">Expiry Date</Label>
                <Input type="date" value={formData.expiry_date} onChange={(e) => setFormData(p => ({...p, expiry_date: e.target.value}))} />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowDialog(false)}>Cancel</Button>
              <Button type="submit">Add Item</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
      {/* Adjust Dialog */}
      <Dialog open={showAdjustDialog} onOpenChange={setShowAdjustDialog}>
        <DialogContent>
          <DialogHeader><DialogTitle>Adjust Inventory - {selectedItem?.ingredient_name}</DialogTitle></DialogHeader>
          <form onSubmit={handleAdjust} className="space-y-4">
            <div className="rounded-sm bg-muted p-3">
              <p className="text-sm text-muted-foreground">Current: <span className="font-mono font-medium">{selectedItem?.quantity} {selectedItem?.unit}</span></p>
            </div>
            <div className="space-y-2">
              <Label className="form-label">Movement Type</Label>
              <Select value={adjustData.movement_type} onValueChange={(v) => setAdjustData(p => ({...p, movement_type: v}))}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="receipt">Receipt (Add)</SelectItem>
                  <SelectItem value="issue">Issue (Remove)</SelectItem>
                  <SelectItem value="adjustment">Adjustment (Set)</SelectItem>
                  <SelectItem value="waste">Waste</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label className="form-label">Quantity *</Label>
              <Input type="number" step="0.01" value={adjustData.quantity} onChange={(e) => setAdjustData(p => ({...p, quantity: e.target.value}))} required />
            </div>
            <div className="space-y-2">
              <Label className="form-label">Notes</Label>
              <Input value={adjustData.notes} onChange={(e) => setAdjustData(p => ({...p, notes: e.target.value}))} placeholder="Optional notes" />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowAdjustDialog(false)}>Cancel</Button>
              <Button type="submit">Apply</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default InventoryPage;
