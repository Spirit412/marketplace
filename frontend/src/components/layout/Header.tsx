import { Link } from "@tanstack/react-router";
import {
    Bell,
    LogOut,
    Menu,
    Moon,
    Package,
    Search,
    ShoppingCart,
    Sun,
    User as UserIcon,
} from "lucide-react";
import { useDispatch, useSelector } from "react-redux";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { selectTheme, setTheme } from "@/store/ui-slice";
import { clearAuth } from "@/store/auth-slice";
import type { RootState } from "@/store";
import { Sidebar } from "./Sidebar";
import { CartDrawer } from "@/features/cart/CartDrawer";
import type { Role } from "@/types";

const ROLE_LABELS: Record<Role, string> = {
    customer: "Покупатель",
    seller: "Продавец",
    moderator: "Модератор",
    admin: "Администратор",
    super_admin: "Супер-админ",
};

const ROLE_LINKS: Record<
    Role,
    { label: string; to: string; icon: React.ComponentType<{ className?: string }> }[]
> = {
    customer: [
        { label: "Каталог", to: "/products", icon: Package },
        { label: "Корзина", to: "/cart", icon: ShoppingCart },
        { label: "Мои заказы", to: "/orders", icon: Package },
    ],
    seller: [
        { label: "Каталог", to: "/products", icon: Package },
        { label: "Корзина", to: "/cart", icon: ShoppingCart },
        { label: "Мои заказы", to: "/orders", icon: Package },
        { label: "Мои товары", to: "/seller/products", icon: Package },
        { label: "Склады", to: "/seller/inventory", icon: Package },
        { label: "Импорт", to: "/seller/imports", icon: Package },
        { label: "Отчёты", to: "/seller/reports", icon: Package },
    ],
    moderator: [
        { label: "Каталог", to: "/products", icon: Package },
        { label: "Заказы", to: "/orders", icon: Package },
    ],
    admin: [
        { label: "Каталог", to: "/products", icon: Package },
        { label: "Заказы", to: "/orders", icon: Package },
        { label: "Пользователи", to: "/admin/users", icon: UserIcon },
        { label: "Роли и права", to: "/admin/roles", icon: UserIcon },
        { label: "Товары", to: "/seller/products", icon: Package },
        { label: "Склады", to: "/seller/inventory", icon: Package },
        { label: "Отчёты", to: "/seller/reports", icon: Package },
    ],
    super_admin: [
        { label: "Каталог", to: "/products", icon: Package },
        { label: "Заказы", to: "/orders", icon: Package },
        { label: "Пользователи", to: "/admin/users", icon: UserIcon },
        { label: "Роли и права", to: "/admin/roles", icon: UserIcon },
        { label: "Товары", to: "/seller/products", icon: Package },
        { label: "Склады", to: "/seller/inventory", icon: Package },
        { label: "Отчёты", to: "/seller/reports", icon: Package },
    ],
};

export function Header() {
    const dispatch = useDispatch();
    const theme = useSelector(selectTheme);
    const profile = useSelector((s: RootState) => s.auth.profile);
    const is_authenticated = useSelector((s: RootState) => s.auth.is_authenticated);

    const role = profile?.role ?? "customer";
    const initials = profile?.email.slice(0, 2).toUpperCase() ?? "?";

    const handleLogout = () => {
        dispatch(clearAuth());
        window.location.href = "/login";
    };

    const toggleTheme = () => {
        const next = theme === "dark" ? "light" : "dark";
        dispatch(setTheme(next));
        document.documentElement.classList.toggle("dark", next === "dark");
    };

    return (
        <header className="bg-background/95 supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50 border-b backdrop-blur">
            <div className="flex h-14 items-center gap-4 px-4">
                {/* Mobile sidebar trigger */}
                <Sheet>
                    <SheetTrigger asChild>
                        <Button variant="ghost" size="icon" className="md:hidden">
                            <Menu className="size-5" />
                        </Button>
                    </SheetTrigger>
                    <SheetContent side="left" className="w-64 p-0">
                        <Sidebar />
                    </SheetContent>
                </Sheet>

                {/* Logo */}
                <Link to="/" className="flex shrink-0 items-center gap-2 text-lg font-bold">
                    <ShoppingCart className="size-6" />
                    <span className="hidden sm:inline">Marketplace</span>
                </Link>

                {/* Search */}
                <div className="hidden max-w-md flex-1 items-center md:flex">
                    <Search className="text-muted-foreground mr-2 size-4 shrink-0" />
                    <Input
                        placeholder="Поиск товаров..."
                        className="h-8 border-none shadow-none focus-visible:ring-0"
                    />
                </div>

                <div className="flex-1 md:hidden" />

                {is_authenticated ? (
                    <div className="flex items-center gap-1">
                        <CartDrawer />
                        <Button variant="ghost" size="icon">
                            <Bell className="size-5" />
                        </Button>
                        <Button variant="ghost" size="icon" onClick={toggleTheme}>
                            {theme === "dark" ? (
                                <Sun className="size-5" />
                            ) : (
                                <Moon className="size-5" />
                            )}
                        </Button>
                        <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon" className="rounded-full">
                                    <Avatar className="size-8">
                                        <AvatarFallback>{initials}</AvatarFallback>
                                    </Avatar>
                                </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end" className="w-56">
                                <DropdownMenuLabel>
                                    <p className="text-sm font-medium">{profile?.email}</p>
                                    <p className="text-muted-foreground text-xs">
                                        {ROLE_LABELS[role]}
                                    </p>
                                </DropdownMenuLabel>
                                <DropdownMenuSeparator />
                                {ROLE_LINKS[role].map((link) => (
                                    <DropdownMenuItem key={link.to} asChild>
                                        <Link to={link.to} className="cursor-pointer">
                                            <link.icon className="mr-2 size-4" />
                                            {link.label}
                                        </Link>
                                    </DropdownMenuItem>
                                ))}
                                <DropdownMenuSeparator />
                                <DropdownMenuItem
                                    onClick={handleLogout}
                                    className="text-destructive"
                                >
                                    <LogOut className="mr-2 size-4" />
                                    Выйти
                                </DropdownMenuItem>
                            </DropdownMenuContent>
                        </DropdownMenu>
                    </div>
                ) : (
                    <div className="flex items-center gap-2">
                        <Button variant="ghost" size="icon" onClick={toggleTheme}>
                            {theme === "dark" ? (
                                <Sun className="size-5" />
                            ) : (
                                <Moon className="size-5" />
                            )}
                        </Button>
                        <Link to="/login">
                            <Button variant="outline" size="sm">
                                Войти
                            </Button>
                        </Link>
                    </div>
                )}
            </div>
        </header>
    );
}
