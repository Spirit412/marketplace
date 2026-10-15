import { createFileRoute, Link } from "@tanstack/react-router";
import { useSelector } from "react-redux";
import { ArrowRight, ClipboardList, LogIn, Package, ShoppingCart } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { RootState } from "@/store";
import type { Role } from "@/types";
import { HeroBlock } from "@/components/blocks/HeroBlock";
import { StatsBlock } from "@/components/blocks/StatsBlock";
import { PricingBlock } from "@/components/blocks/PricingBlock";

const ROLE_GREETINGS: Record<Role, { title: string; subtitle: string }> = {
    customer: {
        title: "Добро пожаловать!",
        subtitle: "Просматривайте каталог, оформляйте заказы.",
    },
    seller: {
        title: "Панель продавца",
        subtitle: "Управляйте товарами, складом, импортом и отчётами.",
    },
    moderator: { title: "Панель модератора", subtitle: "Проверяйте товары, отслеживайте заказы." },
    admin: {
        title: "Панель администратора",
        subtitle: "Управляйте пользователями, ролями и правами.",
    },
    super_admin: {
        title: "Панель супер-администратора",
        subtitle: "Полный доступ ко всем функциям.",
    },
};

export const Route = createFileRoute("/")({
    component: IndexPage,
});

function IndexPage() {
    const is_authenticated = useSelector((s: RootState) => s.auth.is_authenticated);

    if (!is_authenticated) {
        return (
            <div>
                <HeroBlock />
                <section className="py-16">
                    <div className="container mx-auto max-w-6xl px-4 text-center">
                        <Button asChild size="lg" className="gap-2">
                            <Link to="/login">
                                <LogIn className="size-5" />
                                Войти в аккаунт
                            </Link>
                        </Button>
                    </div>
                </section>
                <PricingBlock />
            </div>
        );
    }

    return <AuthenticatedDashboard />;
}

function AuthenticatedDashboard() {
    const profile = useSelector((s: RootState) => s.auth.profile);
    const role = profile?.role ?? "customer";
    const greeting = ROLE_GREETINGS[role];

    return (
        <div className="space-y-8">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">{greeting.title}</h1>
                <p className="text-muted-foreground mt-1">{greeting.subtitle}</p>
            </div>

            <StatsBlock products_count={0} orders_count={0} sellers_count={0} customers_count={0} />

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                <QuickCard
                    title="Каталог товаров"
                    description="Поиск и просмотр товаров"
                    icon={Package}
                    to="/products"
                />
                <QuickCard
                    title="Корзина"
                    description="Ваши выбранные товары"
                    icon={ShoppingCart}
                    to="/cart"
                />
                <QuickCard
                    title="Мои заказы"
                    description="История и статусы заказов"
                    icon={ClipboardList}
                    to="/orders"
                />
                {(role === "seller" || role === "admin" || role === "super_admin") && (
                    <QuickCard
                        title="Мои товары"
                        description="Управление товарами"
                        icon={Package}
                        to="/seller/products"
                    />
                )}
                {(role === "admin" || role === "super_admin") && (
                    <QuickCard
                        title="Пользователи"
                        description="Управление пользователями"
                        icon={Package}
                        to="/admin/users"
                    />
                )}
            </div>
        </div>
    );
}

function QuickCard({
    title,
    description,
    icon: Icon,
    to,
}: {
    title: string;
    description: string;
    icon: React.ComponentType<{ className?: string }>;
    to: string;
}) {
    return (
        <Card className="group transition-shadow hover:shadow-md">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-lg">{title}</CardTitle>
                <Icon className="text-muted-foreground size-5" />
            </CardHeader>
            <CardContent>
                <p className="text-muted-foreground text-sm">{description}</p>
                <Button variant="link" className="mt-2 h-auto p-0" asChild>
                    <a href={to}>
                        Перейти <ArrowRight className="ml-1 size-3" />
                    </a>
                </Button>
            </CardContent>
        </Card>
    );
}
