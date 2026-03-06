import React, { useState, useEffect } from 'react';
import { Header } from '../components/layout';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '../components/ui/table';
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '../components/ui/dialog';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '../components/ui/select';
import { ingredientsAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { Plus, Search, Package, Loader2, Edit, Trash2, AlertTriangle } from 'lucide-react';

const CATEGORIES = [
  'produce', 'meat', 'seafood', 'dairy', 'grains', 'spices',
  'oils', 'sauces', 'beverages', 'frozen', 'canned', 'dry_goods', 'other'
];

export const IngredientsPage = () => {
  const { hasRole } = useAuth();
  const [ingredients, setIngredients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [showDialog, setShowDialog] = useState(false);
  const [editingIngredient, setEditingIngredient] = useState(null);
  const [formData, setFormData] = useState({
    name: '', category: 'other', default_unit: 'unit', cost_per_unit: '',
    allergens: '', is_perishable: false, shelf_life_days: '',
  });

  const fetchIngredients = async () => {
    setLoading(true);
    try {
      const params = {};
      if (search) params.search = search;
      if (categoryFilter !== 'all') params.category = categoryFilter;
      const response = await ingredientsAPI.list(params);
      setIngredients(response.data);
    } catch (err) {
      console.error('Failed to fetch ingredients:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(fetchIngredients, 300);
    return () => clearTimeout(timer);
  }, [search, categoryFilter]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        cost_per_unit: formData.cost_per_unit ? parseFloat(formData.cost_per_unit) : null,
        shelf_life_days: formData.shelf_life_days ? parseInt(formData.shelf_life_days) : null,
        allergens: formData.allergens ? formData.allergens.split(',').map(s => s.trim()) : [],
      };
      if (editingIngredient) {
        await ingredientsAPI.update(editingIngredient.id, payload);
      } else {
        await ingredientsAPI.create(payload);
      }
      setShowDialog(false);
      resetForm();
      fetchIngredients();
    } catch (err) {
      console.error('Failed to save ingredient:', err);
    }
  };

  const handleEdit = (ing) => {
    setEditingIngredient(ing);
    setFormData({
      name: ing.name, category: ing.category, default_unit: ing.default_unit,
      cost_per_unit: ing.cost_per_unit?.toString() || '',
      allergens: ing.allergens?.join(', ') || '',
      is_perishable: ing.is_perishable, shelf_life_days: ing.shelf_life_days?.toString() || '',
    });
    setShowDialog(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this ingredient?')) return;
    try {
      await ingredientsAPI.delete(id);
      fetchIngredients();
    } catch (err) {
      console.error('Failed to delete:', err);
    }
  };

  const resetForm = () => {
    setEditingIngredient(null);
    setFormData({ name: '', category: 'other', default_unit: 'unit', cost_per_unit: '', allergens: '', is_perishable: false, shelf_life_days: '' });
  };

  return (
    <div className="flex min-h-screen flex-col" data-testid="ingredients-page">
      <Header title="Ingredients" subtitle="Manage your ingredient database" />
      <div className="flex-1 space-y-6 p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-1 items-center gap-2">
            <div className="relative max-w-sm flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input placeholder="Search ingredients..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" data-testid="ingredient-search" />
            </div>
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-36"><SelectValue placeholder="Category" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                {CATEGORIES.map(cat => <SelectItem key={cat} value={cat} className="capitalize">{cat.replace('_', ' ')}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          {hasRole(['admin', 'kitchen_manager', 'chef', 'procurement_manager']) && (
            <Button onClick={() => { resetForm(); setShowDialog(true); }} data-testid="new-ingredient-btn">
              <Plus className="mr-2 h-4 w-4" />New Ingredient
            </Button>
          )}
        </div>
        <Card>
          <CardContent className="p-0">
            {loading ? (
              <div className="flex h-64 items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-primary" /></div>
            ) : ingredients.length === 0 ? (
              <div className="flex h-64 flex-col items-center justify-center text-muted-foreground">
                <Package className="mb-4 h-12 w-12" /><p>No ingredients found</p>
              </div>
            ) : (
              <Table className="data-table">
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead><TableHead>Category</TableHead><TableHead>Unit</TableHead>
                    <TableHead>Cost</TableHead><TableHead>Allergens</TableHead><TableHead className="w-20"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {ingredients.map((ing) => (
                    <TableRow key={ing.id}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {ing.is_perishable && <AlertTriangle className="h-4 w-4 text-amber-500" title="Perishable" />}
                          <span className="font-medium">{ing.name}</span>
                        </div>
                      </TableCell>
                      <TableCell className="capitalize">{ing.category.replace('_', ' ')}</TableCell>
                      <TableCell className="font-mono">{ing.default_unit}</TableCell>
                      <TableCell className="font-mono">{ing.cost_per_unit ? `$${ing.cost_per_unit.toFixed(2)}` : '-'}</TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {ing.allergens?.slice(0, 2).map(a => <Badge key={a} className="badge-warning text-xs">{a}</Badge>)}
                          {ing.allergens?.length > 2 && <Badge variant="outline">+{ing.allergens.length - 2}</Badge>}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          <Button variant="ghost" size="icon" onClick={() => handleEdit(ing)}><Edit className="h-4 w-4" /></Button>
                          <Button variant="ghost" size="icon" onClick={() => handleDelete(ing.id)}><Trash2 className="h-4 w-4" /></Button>
                        </div>
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
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingIngredient ? 'Edit Ingredient' : 'New Ingredient'}</DialogTitle>
            <DialogDescription>Fill in the ingredient details</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label className="form-label">Name *</Label>
              <Input value={formData.name} onChange={(e) => setFormData(p => ({...p, name: e.target.value}))} required data-testid="ingredient-name-input" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="form-label">Category</Label>
                <Select value={formData.category} onValueChange={(v) => setFormData(p => ({...p, category: v}))}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>{CATEGORIES.map(cat => <SelectItem key={cat} value={cat} className="capitalize">{cat.replace('_', ' ')}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label className="form-label">Default Unit</Label>
                <Input value={formData.default_unit} onChange={(e) => setFormData(p => ({...p, default_unit: e.target.value}))} placeholder="kg, L, unit" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="form-label">Cost per Unit ($)</Label>
                <Input type="number" step="0.01" value={formData.cost_per_unit} onChange={(e) => setFormData(p => ({...p, cost_per_unit: e.target.value}))} />
              </div>
              <div className="space-y-2">
                <Label className="form-label">Shelf Life (days)</Label>
                <Input type="number" value={formData.shelf_life_days} onChange={(e) => setFormData(p => ({...p, shelf_life_days: e.target.value}))} />
              </div>
            </div>
            <div className="space-y-2">
              <Label className="form-label">Allergens (comma separated)</Label>
              <Input value={formData.allergens} onChange={(e) => setFormData(p => ({...p, allergens: e.target.value}))} placeholder="nuts, dairy, gluten" />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowDialog(false)}>Cancel</Button>
              <Button type="submit" data-testid="save-ingredient-btn">{editingIngredient ? 'Update' : 'Create'}</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default IngredientsPage;
