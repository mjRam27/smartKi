import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { cn } from '../../lib/utils';
import {
  LayoutDashboard,
  ChefHat,
  Package,
  Warehouse,
  Truck,
  ShoppingCart,
  Trash2,
  Factory,
  BarChart3,
  Building2,
  Settings,
  Sparkles,
  Users,
} from 'lucide-react';

const navItems = [
  { label: 'Dashboard', icon: LayoutDashboard, path: '/dashboard', roles: ['admin', 'kitchen_manager', 'chef', 'procurement_manager', 'analyst', 'staff'] },
  { label: 'Recipes', icon: ChefHat, path: '/recipes', roles: ['admin', 'kitchen_manager', 'chef', 'staff'] },
  { label: 'AI Recipe Gen', icon: Sparkles, path: '/recipes/generate', roles: ['admin', 'kitchen_manager', 'chef'] },
  { label: 'Ingredients', icon: Package, path: '/ingredients', roles: ['admin', 'kitchen_manager', 'chef', 'procurement_manager', 'staff'] },
  { label: 'Inventory', icon: Warehouse, path: '/inventory', roles: ['admin', 'kitchen_manager', 'chef', 'staff'] },
  { label: 'Suppliers', icon: Truck, path: '/suppliers', roles: ['admin', 'kitchen_manager', 'procurement_manager'] },
  { label: 'Procurement', icon: ShoppingCart, path: '/procurement', roles: ['admin', 'kitchen_manager', 'procurement_manager', 'chef'] },
  { label: 'Waste Log', icon: Trash2, path: '/waste', roles: ['admin', 'kitchen_manager', 'chef', 'staff'] },
  { label: 'Production', icon: Factory, path: '/production', roles: ['admin', 'kitchen_manager', 'chef', 'staff'] },
  { label: 'Analytics', icon: BarChart3, path: '/analytics', roles: ['admin', 'kitchen_manager', 'analyst'] },
  { label: 'Kitchens', icon: Building2, path: '/kitchens', roles: ['admin', 'kitchen_manager'] },
  { label: 'Settings', icon: Settings, path: '/settings', roles: ['admin', 'kitchen_manager'] },
];

export const Sidebar = () => {
  const { user, hasRole } = useAuth();
  const location = useLocation();
  
  const filteredItems = navItems.filter(item => hasRole(item.roles));

  return (
    <aside 
      className="fixed left-0 top-0 z-30 hidden h-full w-64 flex-col border-r border-border bg-card md:flex"
      data-testid="sidebar"
    >
      {/* Logo */}
      <div className="flex h-16 items-center gap-3 border-b border-border px-6">
        <div className="flex h-9 w-9 items-center justify-center rounded-sm bg-primary">
          <ChefHat className="h-5 w-5 text-primary-foreground" />
        </div>
        <div>
          <h1 className="text-sm font-semibold tracking-tight">Kitchen Intel</h1>
          <p className="text-xs text-muted-foreground">Platform</p>
        </div>
      </div>
      
      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-4">
        <ul className="space-y-1">
          {filteredItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path || 
              (item.path !== '/dashboard' && location.pathname.startsWith(item.path));
            
            return (
              <li key={item.path}>
                <NavLink
                  to={item.path}
                  data-testid={`nav-${item.label.toLowerCase().replace(/\s+/g, '-')}`}
                  className={cn(
                    'flex items-center gap-3 rounded-sm px-3 py-2 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-primary/10 text-primary'
                      : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </NavLink>
              </li>
            );
          })}
        </ul>
      </nav>
      
      {/* User info */}
      <div className="border-t border-border p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-muted">
            <Users className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="flex-1 truncate">
            <p className="truncate text-sm font-medium">
              {user?.first_name} {user?.last_name}
            </p>
            <p className="truncate text-xs text-muted-foreground capitalize">
              {user?.role?.replace('_', ' ')}
            </p>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
