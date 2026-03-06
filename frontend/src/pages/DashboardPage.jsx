import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Header } from '../components/layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { analyticsAPI } from '../services/api';
import { useApp } from '../contexts/AppContext';
import { useAuth } from '../contexts/AuthContext';
import {
  ChefHat,
  Package,
  Truck,
  Warehouse,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  ShoppingCart,
  Trash2,
  DollarSign,
  BarChart3,
  Plus,
  Loader2,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

const COLORS = ['#10b981', '#f97316', '#3b82f6', '#ef4444', '#8b5cf6'];

const StatCard = ({ title, value, subtitle, icon: Icon, trend, trendValue, color = 'primary' }) => (
  <Card className="card-interactive" data-testid={`stat-${title.toLowerCase().replace(/\s+/g, '-')}`}>
    <CardContent className="p-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs uppercase tracking-wider text-muted-foreground">{title}</p>
          <p className="mt-1 font-mono text-2xl font-semibold" data-numeric="true">{value}</p>
          {subtitle && <p className="mt-0.5 text-xs text-muted-foreground">{subtitle}</p>}
          {trend && (
            <div className={`mt-2 flex items-center gap-1 text-xs ${trend === 'up' ? 'text-emerald-500' : 'text-red-500'}`}>
              {trend === 'up' ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
              <span className="font-mono">{trendValue}</span>
            </div>
          )}
        </div>
        <div className={`flex h-10 w-10 items-center justify-center rounded-sm bg-${color}/10`}>
          <Icon className={`h-5 w-5 text-${color}`} />
        </div>
      </div>
    </CardContent>
  </Card>
);

const AlertCard = ({ title, items, type }) => (
  <Card className="card-interactive">
    <CardHeader className="pb-2">
      <CardTitle className="flex items-center gap-2 text-sm font-medium">
        <AlertTriangle className={`h-4 w-4 ${type === 'warning' ? 'text-amber-500' : 'text-red-500'}`} />
        {title}
        {items.length > 0 && (
          <Badge variant="outline" className={type === 'warning' ? 'badge-warning' : 'badge-error'}>
            {items.length}
          </Badge>
        )}
      </CardTitle>
    </CardHeader>
    <CardContent>
      {items.length === 0 ? (
        <p className="text-sm text-muted-foreground">No alerts</p>
      ) : (
        <ul className="space-y-2">
          {items.slice(0, 5).map((item, idx) => (
            <li key={idx} className="flex items-center justify-between text-sm">
              <span className="truncate">{item.ingredient_name || item.name}</span>
              <span className="font-mono text-xs text-muted-foreground">
                {item.quantity} {item.unit}
              </span>
            </li>
          ))}
        </ul>
      )}
    </CardContent>
  </Card>
);

export const DashboardPage = () => {
  const navigate = useNavigate();
  const { selectedKitchen } = useApp();
  const { user } = useAuth();
  const [metrics, setMetrics] = useState(null);
  const [wasteTrends, setWasteTrends] = useState(null);
  const [alerts, setAlerts] = useState({ low_stock: [], expiring_soon: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const params = selectedKitchen ? { kitchen_id: selectedKitchen.id } : {};
        
        const [dashboardRes, wasteRes, alertsRes] = await Promise.all([
          analyticsAPI.dashboard(params),
          analyticsAPI.wasteTrends(params),
          analyticsAPI.inventoryAlerts(params),
        ]);
        
        setMetrics(dashboardRes.data);
        setWasteTrends(wasteRes.data);
        setAlerts(alertsRes.data);
      } catch (err) {
        console.error('Failed to fetch dashboard data:', err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [selectedKitchen]);

  const wasteByReasonData = wasteTrends?.by_reason 
    ? Object.entries(wasteTrends.by_reason).map(([reason, data]) => ({
        name: reason.replace('_', ' '),
        value: data.cost,
        count: data.count,
      }))
    : [];

  if (loading) {
    return (
      <div className="flex min-h-screen flex-col">
        <Header title="Dashboard" subtitle={selectedKitchen?.name || 'All Kitchens'} />
        <div className="flex flex-1 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col" data-testid="dashboard-page">
      <Header 
        title="Dashboard" 
        subtitle={`Welcome back, ${user?.first_name}`}
      />
      
      <div className="flex-1 space-y-6 p-6">
        {/* Quick Actions */}
        <div className="flex flex-wrap gap-2">
          <Button size="sm" onClick={() => navigate('/recipes/generate')} data-testid="quick-ai-recipe">
            <Plus className="mr-1 h-4 w-4" />
            AI Recipe
          </Button>
          <Button size="sm" variant="outline" onClick={() => navigate('/waste')} data-testid="quick-log-waste">
            <Trash2 className="mr-1 h-4 w-4" />
            Log Waste
          </Button>
          <Button size="sm" variant="outline" onClick={() => navigate('/procurement')} data-testid="quick-new-order">
            <ShoppingCart className="mr-1 h-4 w-4" />
            New Order
          </Button>
        </div>
        
        {/* Stats Grid */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="Total Recipes"
            value={metrics?.overview?.recipes || 0}
            icon={ChefHat}
            color="primary"
          />
          <StatCard
            title="Ingredients"
            value={metrics?.overview?.ingredients || 0}
            icon={Package}
            color="secondary"
          />
          <StatCard
            title="Inventory Value"
            value={`$${(metrics?.inventory?.total_value || 0).toLocaleString()}`}
            subtitle={`${metrics?.inventory?.items_count || 0} items`}
            icon={Warehouse}
            color="primary"
          />
          <StatCard
            title="Suppliers"
            value={metrics?.overview?.suppliers || 0}
            icon={Truck}
            color="secondary"
          />
        </div>
        
        {/* Second Row Stats */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="Pending Orders"
            value={metrics?.orders?.pending || 0}
            icon={ShoppingCart}
            color="secondary"
          />
          <StatCard
            title="Weekly Waste Cost"
            value={`$${(metrics?.waste?.weekly_cost || 0).toLocaleString()}`}
            subtitle={`${metrics?.waste?.entries_count || 0} entries`}
            icon={Trash2}
            color="destructive"
          />
          <StatCard
            title="Total Revenue"
            value={`$${(metrics?.production?.total_revenue || 0).toLocaleString()}`}
            icon={DollarSign}
            color="primary"
          />
          <StatCard
            title="Total Profit"
            value={`$${(metrics?.production?.total_profit || 0).toLocaleString()}`}
            icon={BarChart3}
            color="primary"
          />
        </div>
        
        {/* Charts and Alerts Row */}
        <div className="grid gap-4 lg:grid-cols-3">
          {/* Waste Trends Chart */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle className="text-sm font-medium">Waste Trends (Last 30 Days)</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={wasteTrends?.trends || []}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis 
                      dataKey="date" 
                      tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }}
                      tickFormatter={(value) => value.slice(5)}
                    />
                    <YAxis 
                      tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }}
                      tickFormatter={(value) => `$${value}`}
                    />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: 'hsl(var(--card))', 
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '4px',
                      }}
                      formatter={(value) => [`$${value}`, 'Cost']}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="cost" 
                      stroke="hsl(var(--secondary))" 
                      fill="hsl(var(--secondary))" 
                      fillOpacity={0.2}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
          
          {/* Waste by Reason Pie Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Waste by Reason</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                {wasteByReasonData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={wasteByReasonData}
                        cx="50%"
                        cy="50%"
                        innerRadius={40}
                        outerRadius={80}
                        paddingAngle={2}
                        dataKey="value"
                      >
                        {wasteByReasonData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: 'hsl(var(--card))', 
                          border: '1px solid hsl(var(--border))',
                          borderRadius: '4px',
                        }}
                        formatter={(value) => [`$${value}`, 'Cost']}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                    No waste data
                  </div>
                )}
              </div>
              {wasteByReasonData.length > 0 && (
                <div className="mt-2 space-y-1">
                  {wasteByReasonData.map((item, idx) => (
                    <div key={idx} className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <div 
                          className="h-2 w-2 rounded-full" 
                          style={{ backgroundColor: COLORS[idx % COLORS.length] }}
                        />
                        <span className="capitalize">{item.name}</span>
                      </div>
                      <span className="font-mono">${item.value.toFixed(0)}</span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
        
        {/* Alerts Row */}
        <div className="grid gap-4 md:grid-cols-2">
          <AlertCard 
            title="Low Stock Items" 
            items={alerts.low_stock} 
            type="warning"
          />
          <AlertCard 
            title="Expiring Soon" 
            items={alerts.expiring_soon} 
            type="error"
          />
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
