import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Header } from '../components/layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { recipesAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import {
  Plus,
  Search,
  MoreVertical,
  Eye,
  Edit,
  Trash2,
  Sparkles,
  ChefHat,
  Clock,
  DollarSign,
  Check,
  Loader2,
  Filter,
} from 'lucide-react';

const statusColors = {
  active: 'badge-success',
  draft: 'badge-info',
  pending_review: 'badge-warning',
  archived: 'badge-error',
};

export const RecipesPage = () => {
  const navigate = useNavigate();
  const { hasRole } = useAuth();
  const [recipes, setRecipes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [cuisineFilter, setCuisineFilter] = useState('all');

  const fetchRecipes = async () => {
    setLoading(true);
    try {
      const params = {};
      if (search) params.search = search;
      if (statusFilter !== 'all') params.status = statusFilter;
      if (cuisineFilter !== 'all') params.cuisine_type = cuisineFilter;
      
      const response = await recipesAPI.list(params);
      setRecipes(response.data);
    } catch (err) {
      console.error('Failed to fetch recipes:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecipes();
  }, [statusFilter, cuisineFilter]);

  useEffect(() => {
    const timer = setTimeout(() => {
      if (search !== undefined) fetchRecipes();
    }, 300);
    return () => clearTimeout(timer);
  }, [search]);

  const handleApprove = async (id) => {
    try {
      await recipesAPI.approve(id);
      fetchRecipes();
    } catch (err) {
      console.error('Failed to approve recipe:', err);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to archive this recipe?')) return;
    try {
      await recipesAPI.delete(id);
      fetchRecipes();
    } catch (err) {
      console.error('Failed to delete recipe:', err);
    }
  };

  const cuisines = [...new Set(recipes.map(r => r.cuisine_type).filter(Boolean))];

  return (
    <div className="flex min-h-screen flex-col" data-testid="recipes-page">
      <Header title="Recipes" subtitle="Manage your recipe library" />
      
      <div className="flex-1 space-y-6 p-6">
        {/* Actions Bar */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-1 items-center gap-2">
            <div className="relative max-w-sm flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search recipes..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
                data-testid="recipe-search"
              />
            </div>
            
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-36" data-testid="status-filter">
                <Filter className="mr-2 h-4 w-4" />
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="draft">Draft</SelectItem>
                <SelectItem value="pending_review">Pending Review</SelectItem>
                <SelectItem value="archived">Archived</SelectItem>
              </SelectContent>
            </Select>
            
            {cuisines.length > 0 && (
              <Select value={cuisineFilter} onValueChange={setCuisineFilter}>
                <SelectTrigger className="w-36">
                  <SelectValue placeholder="Cuisine" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Cuisines</SelectItem>
                  {cuisines.map(cuisine => (
                    <SelectItem key={cuisine} value={cuisine}>{cuisine}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>
          
          <div className="flex gap-2">
            {hasRole(['admin', 'kitchen_manager', 'chef']) && (
              <>
                <Button 
                  variant="outline"
                  onClick={() => navigate('/recipes/generate')}
                  data-testid="ai-generate-btn"
                >
                  <Sparkles className="mr-2 h-4 w-4" />
                  AI Generate
                </Button>
                <Button onClick={() => navigate('/recipes/new')} data-testid="new-recipe-btn">
                  <Plus className="mr-2 h-4 w-4" />
                  New Recipe
                </Button>
              </>
            )}
          </div>
        </div>
        
        {/* Recipes Table */}
        <Card>
          <CardContent className="p-0">
            {loading ? (
              <div className="flex h-64 items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
              </div>
            ) : recipes.length === 0 ? (
              <div className="flex h-64 flex-col items-center justify-center text-muted-foreground">
                <ChefHat className="mb-4 h-12 w-12" />
                <p>No recipes found</p>
                <Button 
                  variant="link" 
                  className="mt-2"
                  onClick={() => navigate('/recipes/generate')}
                >
                  Generate your first recipe with AI
                </Button>
              </div>
            ) : (
              <Table className="data-table">
                <TableHeader>
                  <TableRow>
                    <TableHead>Recipe</TableHead>
                    <TableHead>Cuisine</TableHead>
                    <TableHead>Servings</TableHead>
                    <TableHead>Time</TableHead>
                    <TableHead>Cost</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="w-12"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {recipes.map((recipe) => (
                    <TableRow key={recipe.id} data-testid={`recipe-row-${recipe.id}`}>
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <div className="flex h-10 w-10 items-center justify-center rounded-sm bg-muted">
                            {recipe.is_ai_generated ? (
                              <Sparkles className="h-5 w-5 text-primary" />
                            ) : (
                              <ChefHat className="h-5 w-5 text-muted-foreground" />
                            )}
                          </div>
                          <div>
                            <p className="font-medium">{recipe.title}</p>
                            {recipe.category && (
                              <p className="text-xs text-muted-foreground">{recipe.category}</p>
                            )}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>{recipe.cuisine_type || '-'}</TableCell>
                      <TableCell className="font-mono">{recipe.servings}</TableCell>
                      <TableCell>
                        {recipe.total_time_minutes ? (
                          <div className="flex items-center gap-1 text-muted-foreground">
                            <Clock className="h-3 w-3" />
                            <span className="font-mono">{recipe.total_time_minutes}m</span>
                          </div>
                        ) : '-'}
                      </TableCell>
                      <TableCell>
                        {recipe.estimated_cost_per_serving ? (
                          <div className="flex items-center gap-1">
                            <DollarSign className="h-3 w-3 text-muted-foreground" />
                            <span className="font-mono">{recipe.estimated_cost_per_serving.toFixed(2)}</span>
                          </div>
                        ) : '-'}
                      </TableCell>
                      <TableCell>
                        <Badge className={statusColors[recipe.status] || 'badge-info'}>
                          {recipe.status.replace('_', ' ')}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => navigate(`/recipes/${recipe.id}`)}>
                              <Eye className="mr-2 h-4 w-4" />
                              View
                            </DropdownMenuItem>
                            {hasRole(['admin', 'kitchen_manager', 'chef']) && (
                              <>
                                <DropdownMenuItem onClick={() => navigate(`/recipes/${recipe.id}/edit`)}>
                                  <Edit className="mr-2 h-4 w-4" />
                                  Edit
                                </DropdownMenuItem>
                                {recipe.status === 'pending_review' && (
                                  <DropdownMenuItem onClick={() => handleApprove(recipe.id)}>
                                    <Check className="mr-2 h-4 w-4" />
                                    Approve
                                  </DropdownMenuItem>
                                )}
                                <DropdownMenuItem 
                                  onClick={() => handleDelete(recipe.id)}
                                  className="text-destructive"
                                >
                                  <Trash2 className="mr-2 h-4 w-4" />
                                  Archive
                                </DropdownMenuItem>
                              </>
                            )}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default RecipesPage;
