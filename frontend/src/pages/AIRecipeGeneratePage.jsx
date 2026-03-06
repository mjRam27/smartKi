import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Header } from '../components/layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Badge } from '../components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { recipesAPI } from '../services/api';
import { useApp } from '../contexts/AppContext';
import {
  Sparkles,
  Loader2,
  ChefHat,
  Clock,
  DollarSign,
  Users,
  AlertTriangle,
  Check,
  X,
  Plus,
} from 'lucide-react';

const CUISINES = [
  'Italian', 'Mexican', 'Asian', 'Mediterranean', 'French', 'Indian', 
  'American', 'Japanese', 'Thai', 'Greek', 'Spanish', 'Middle Eastern'
];

const DIETARY = [
  'vegetarian', 'vegan', 'gluten-free', 'keto', 'low-carb', 
  'dairy-free', 'nut-free', 'halal', 'kosher'
];

export const AIRecipeGeneratePage = () => {
  const navigate = useNavigate();
  const { selectedKitchen, kitchens } = useApp();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [generatedRecipe, setGeneratedRecipe] = useState(null);
  
  const [formData, setFormData] = useState({
    recipe_name: '',
    short_description: '',
    cuisine_type: '',
    dietary_preference: '',
    serving_count: 4,
    include_ingredients: '',
    avoid_ingredients: '',
    kitchen_id: selectedKitchen?.id || '',
  });

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleGenerate = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setGeneratedRecipe(null);
    
    try {
      const payload = {
        recipe_name: formData.recipe_name,
        short_description: formData.short_description || undefined,
        cuisine_type: formData.cuisine_type || undefined,
        dietary_preference: formData.dietary_preference || undefined,
        serving_count: parseInt(formData.serving_count),
        include_ingredients: formData.include_ingredients 
          ? formData.include_ingredients.split(',').map(s => s.trim()).filter(Boolean)
          : [],
        avoid_ingredients: formData.avoid_ingredients 
          ? formData.avoid_ingredients.split(',').map(s => s.trim()).filter(Boolean)
          : [],
        kitchen_id: formData.kitchen_id || undefined,
      };
      
      const response = await recipesAPI.generate(payload);
      
      if (response.data.success) {
        setGeneratedRecipe(response.data.recipe);
      } else {
        setError(response.data.error || 'Failed to generate recipe');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate recipe');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col" data-testid="ai-recipe-generate-page">
      <Header title="AI Recipe Generation" subtitle="Create recipes with artificial intelligence" />
      
      <div className="flex-1 p-6">
        <div className="mx-auto max-w-5xl">
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Input Form */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-primary" />
                  Generate Recipe
                </CardTitle>
                <CardDescription>
                  Describe what you want and let AI create a professional recipe
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleGenerate} className="space-y-4">
                  {error && (
                    <div className="flex items-center gap-2 rounded-sm bg-destructive/10 p-3 text-sm text-destructive">
                      <AlertTriangle className="h-4 w-4" />
                      {error}
                    </div>
                  )}
                  
                  <div className="space-y-2">
                    <Label className="form-label">Recipe Name *</Label>
                    <Input
                      placeholder="e.g., Creamy Tuscan Chicken"
                      value={formData.recipe_name}
                      onChange={(e) => handleChange('recipe_name', e.target.value)}
                      required
                      data-testid="recipe-name-input"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label className="form-label">Description (Optional)</Label>
                    <Textarea
                      placeholder="Brief description of what you're looking for..."
                      value={formData.short_description}
                      onChange={(e) => handleChange('short_description', e.target.value)}
                      rows={2}
                      data-testid="recipe-description-input"
                    />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label className="form-label">Cuisine Type</Label>
                      <Select 
                        value={formData.cuisine_type} 
                        onValueChange={(value) => handleChange('cuisine_type', value)}
                      >
                        <SelectTrigger data-testid="cuisine-select">
                          <SelectValue placeholder="Select cuisine" />
                        </SelectTrigger>
                        <SelectContent>
                          {CUISINES.map(cuisine => (
                            <SelectItem key={cuisine} value={cuisine}>{cuisine}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div className="space-y-2">
                      <Label className="form-label">Dietary Preference</Label>
                      <Select 
                        value={formData.dietary_preference} 
                        onValueChange={(value) => handleChange('dietary_preference', value)}
                      >
                        <SelectTrigger data-testid="dietary-select">
                          <SelectValue placeholder="Select dietary" />
                        </SelectTrigger>
                        <SelectContent>
                          {DIETARY.map(diet => (
                            <SelectItem key={diet} value={diet} className="capitalize">{diet}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label className="form-label">Servings</Label>
                      <Input
                        type="number"
                        min="1"
                        max="100"
                        value={formData.serving_count}
                        onChange={(e) => handleChange('serving_count', e.target.value)}
                        data-testid="servings-input"
                      />
                    </div>
                    
                    {kitchens.length > 0 && (
                      <div className="space-y-2">
                        <Label className="form-label">Kitchen</Label>
                        <Select 
                          value={formData.kitchen_id} 
                          onValueChange={(value) => handleChange('kitchen_id', value)}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select kitchen" />
                          </SelectTrigger>
                          <SelectContent>
                            {kitchens.map(kitchen => (
                              <SelectItem key={kitchen.id} value={kitchen.id}>
                                {kitchen.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    )}
                  </div>
                  
                  <div className="space-y-2">
                    <Label className="form-label">Include Ingredients (comma separated)</Label>
                    <Input
                      placeholder="e.g., chicken, spinach, sun-dried tomatoes"
                      value={formData.include_ingredients}
                      onChange={(e) => handleChange('include_ingredients', e.target.value)}
                      data-testid="include-ingredients-input"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label className="form-label">Avoid Ingredients (comma separated)</Label>
                    <Input
                      placeholder="e.g., nuts, shellfish, gluten"
                      value={formData.avoid_ingredients}
                      onChange={(e) => handleChange('avoid_ingredients', e.target.value)}
                      data-testid="avoid-ingredients-input"
                    />
                  </div>
                  
                  <Button 
                    type="submit" 
                    className="w-full" 
                    disabled={loading || !formData.recipe_name}
                    data-testid="generate-btn"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Generating recipe...
                      </>
                    ) : (
                      <>
                        <Sparkles className="mr-2 h-4 w-4" />
                        Generate Recipe
                      </>
                    )}
                  </Button>
                </form>
              </CardContent>
            </Card>
            
            {/* Generated Recipe Preview */}
            <Card className={!generatedRecipe ? 'opacity-60' : ''}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ChefHat className="h-5 w-5" />
                  Generated Recipe
                </CardTitle>
                <CardDescription>
                  {generatedRecipe 
                    ? 'Review your AI-generated recipe' 
                    : 'Your recipe will appear here'
                  }
                </CardDescription>
              </CardHeader>
              <CardContent>
                {!generatedRecipe ? (
                  <div className="flex h-64 flex-col items-center justify-center text-muted-foreground">
                    <Sparkles className="mb-4 h-12 w-12" />
                    <p>Fill the form and click Generate</p>
                  </div>
                ) : (
                  <div className="space-y-4" data-testid="generated-recipe">
                    <div>
                      <h3 className="text-xl font-semibold">{generatedRecipe.title}</h3>
                      <p className="mt-1 text-sm text-muted-foreground">
                        {generatedRecipe.description}
                      </p>
                    </div>
                    
                    {/* Meta Info */}
                    <div className="flex flex-wrap gap-4 text-sm">
                      {generatedRecipe.total_time_minutes && (
                        <div className="flex items-center gap-1">
                          <Clock className="h-4 w-4 text-muted-foreground" />
                          <span className="font-mono">{generatedRecipe.total_time_minutes} min</span>
                        </div>
                      )}
                      <div className="flex items-center gap-1">
                        <Users className="h-4 w-4 text-muted-foreground" />
                        <span className="font-mono">{generatedRecipe.servings} servings</span>
                      </div>
                      {generatedRecipe.estimated_cost_per_serving && (
                        <div className="flex items-center gap-1">
                          <DollarSign className="h-4 w-4 text-muted-foreground" />
                          <span className="font-mono">${generatedRecipe.estimated_cost_per_serving.toFixed(2)}/serving</span>
                        </div>
                      )}
                    </div>
                    
                    {/* Tags */}
                    <div className="flex flex-wrap gap-1">
                      {generatedRecipe.cuisine_type && (
                        <Badge variant="outline">{generatedRecipe.cuisine_type}</Badge>
                      )}
                      {generatedRecipe.category && (
                        <Badge variant="outline">{generatedRecipe.category}</Badge>
                      )}
                      {generatedRecipe.dietary_preferences?.map(diet => (
                        <Badge key={diet} className="badge-success">{diet}</Badge>
                      ))}
                    </div>
                    
                    {/* Allergens */}
                    {generatedRecipe.allergens?.length > 0 && (
                      <div>
                        <p className="text-xs uppercase tracking-wider text-muted-foreground">Allergens</p>
                        <div className="mt-1 flex flex-wrap gap-1">
                          {generatedRecipe.allergens.map(allergen => (
                            <Badge key={allergen} className="badge-warning">{allergen}</Badge>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {/* Ingredients */}
                    <div>
                      <p className="text-xs uppercase tracking-wider text-muted-foreground">Ingredients</p>
                      <ul className="mt-2 space-y-1">
                        {generatedRecipe.ingredients?.slice(0, 6).map((ing, idx) => (
                          <li key={idx} className="flex items-center gap-2 text-sm">
                            <Check className="h-3 w-3 text-primary" />
                            <span className="font-mono">{ing.quantity} {ing.unit}</span>
                            <span>{ing.name}</span>
                          </li>
                        ))}
                        {generatedRecipe.ingredients?.length > 6 && (
                          <li className="text-sm text-muted-foreground">
                            +{generatedRecipe.ingredients.length - 6} more ingredients
                          </li>
                        )}
                      </ul>
                    </div>
                    
                    {/* Instructions Preview */}
                    <div>
                      <p className="text-xs uppercase tracking-wider text-muted-foreground">Instructions</p>
                      <ol className="mt-2 space-y-1 text-sm">
                        {generatedRecipe.instructions?.slice(0, 3).map((step, idx) => (
                          <li key={idx} className="flex gap-2">
                            <span className="font-mono text-primary">{idx + 1}.</span>
                            <span className="line-clamp-1">{step}</span>
                          </li>
                        ))}
                        {generatedRecipe.instructions?.length > 3 && (
                          <li className="text-muted-foreground">
                            +{generatedRecipe.instructions.length - 3} more steps
                          </li>
                        )}
                      </ol>
                    </div>
                    
                    {/* Actions */}
                    <div className="flex gap-2 pt-4">
                      <Button 
                        onClick={() => navigate(`/recipes/${generatedRecipe.id}`)}
                        className="flex-1"
                        data-testid="view-recipe-btn"
                      >
                        <Check className="mr-2 h-4 w-4" />
                        View Full Recipe
                      </Button>
                      <Button 
                        variant="outline"
                        onClick={() => navigate('/recipes')}
                        data-testid="back-to-recipes-btn"
                      >
                        Back to Recipes
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIRecipeGeneratePage;
