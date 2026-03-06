import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useApp } from '../../contexts/AppContext';
import { Button } from '../ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select';
import { Bell, ChevronDown, LogOut, Settings, User, Building2 } from 'lucide-react';

export const Header = ({ title, subtitle }) => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { kitchens, selectedKitchen, selectKitchen } = useApp();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header 
      className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-border bg-background/80 px-6 backdrop-blur-md"
      data-testid="header"
    >
      <div>
        <h1 className="text-lg font-semibold">{title}</h1>
        {subtitle && <p className="text-sm text-muted-foreground">{subtitle}</p>}
      </div>
      
      <div className="flex items-center gap-4">
        {/* Kitchen Selector */}
        {kitchens.length > 0 && (
          <Select 
            value={selectedKitchen?.id || ''} 
            onValueChange={(value) => {
              const kitchen = kitchens.find(k => k.id === value);
              selectKitchen(kitchen);
            }}
          >
            <SelectTrigger 
              className="w-48 bg-muted/50"
              data-testid="kitchen-selector"
            >
              <Building2 className="mr-2 h-4 w-4" />
              <SelectValue placeholder="Select Kitchen" />
            </SelectTrigger>
            <SelectContent>
              {kitchens.map((kitchen) => (
                <SelectItem key={kitchen.id} value={kitchen.id}>
                  {kitchen.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
        
        {/* Notifications */}
        <Button 
          variant="ghost" 
          size="icon" 
          className="relative"
          data-testid="notifications-btn"
        >
          <Bell className="h-5 w-5" />
          <span className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-secondary text-[10px] font-medium text-secondary-foreground">
            3
          </span>
        </Button>
        
        {/* User Menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button 
              variant="ghost" 
              className="gap-2"
              data-testid="user-menu-btn"
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/20">
                <User className="h-4 w-4 text-primary" />
              </div>
              <span className="hidden text-sm md:inline-block">
                {user?.first_name}
              </span>
              <ChevronDown className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel>
              <div>
                <p className="font-medium">{user?.first_name} {user?.last_name}</p>
                <p className="text-xs text-muted-foreground">{user?.email}</p>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => navigate('/settings')}>
              <Settings className="mr-2 h-4 w-4" />
              Settings
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem 
              onClick={handleLogout}
              className="text-destructive focus:text-destructive"
              data-testid="logout-btn"
            >
              <LogOut className="mr-2 h-4 w-4" />
              Log out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
};

export default Header;
