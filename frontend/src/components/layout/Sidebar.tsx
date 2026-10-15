import { Link, useMatch } from "@tanstack/react-router";
import { useSelector } from "react-redux";
import {
    BarChart3,
    ClipboardList,
    FileUp,
    Package,
    Shield,
    ShoppingCart,
    Store,
    Truck,
    Users,
} from "lucide-react";
import { ScrollArea } from "@radix-ui/react-scroll-area";
import type { RootState } from "@/store";
import type { Role } from "@/types";

interface NavItem {
    label: string;
    to: string;
    icon: React.ComponentType<{ className?: string }>;
    roles: Role[];
}

const NAV_ITEMS: NavItem[] = [
    {
        label: "Каталог",
        to: "/products",
        icon: Store,
        roles: ["customer", "seller", "moderator", "admin", "super_admin"],
    },
    { label: "Корзина", to: "/cart", icon: ShoppingCart, roles: ["customer", "seller"] },
    {
        label: "Мои заказы",
        to: "/orders",
        icon: ClipboardList,
        roles: ["customer", "seller", "moderator", "admin", "super_admin"],
    },
    {
        label: "Мои товары",
        to: "/seller/products",
        icon: Package,
        roles: ["seller", "admin", "super_admin"],
    },
    {
        label: "Склады",
        to: "/seller/inventory",
        icon: Truck,
        roles: ["seller", "admin", "super_admin"],
    },
    { label: "Импорт", to: "/seller/imports", icon: FileUp, roles: ["seller"] },
    {
        label: "Отчёты",
        to: "/seller/reports",
        icon: BarChart3,
        roles: ["seller", "admin", "super_admin"],
    },
    { label: "Пользователи", to: "/admin/users", icon: Users, roles: ["admin", "super_admin"] },
    { label: "Роли и права", to: "/admin/roles", icon: Shield, roles: ["admin", "super_admin"] },
];

export function Sidebar() {
    const profile = useSelector((s: RootState) => s.auth.profile);
    const role = profile?.role ?? "customer";

    const visible_items = NAV_ITEMS.filter((item) => item.roles.includes(role));

    return (
        <aside className="bg-background hidden w-56 shrink-0 border-r md:block">
            <ScrollArea className="h-[calc(100vh-3.5rem)]">
                <nav className="flex flex-col gap-1 p-3">
                    {visible_items.map((item) => (
                        <SidebarLink key={item.to} item={item} />
                    ))}
                </nav>
            </ScrollArea>
        </aside>
    );
}

function SidebarLink({ item }: { item: NavItem }) {
    // TanStack Router: проверяем, активен ли путь (начинается с to)
    const match = useMatch({ from: item.to as never, shouldThrow: false });

    return (
        <Link
            to={item.to}
            className={
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors " +
                (match
                    ? "bg-accent text-accent-foreground font-medium"
                    : "text-muted-foreground hover:bg-accent/50 hover:text-foreground")
            }
        >
            <item.icon className="size-4 shrink-0" />
            <span>{item.label}</span>
        </Link>
    );
}
