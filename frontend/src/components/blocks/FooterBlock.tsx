import { Link } from "@tanstack/react-router";
import { ShoppingCart } from "lucide-react";
import { Separator } from "@/components/ui/separator";

const FOOTER_LINKS = {
    Покупателям: [
        { label: "Каталог", to: "/products" },
        { label: "Корзина", to: "/cart" },
        { label: "Мои заказы", to: "/orders" },
    ],
    Продавцам: [
        { label: "Мои товары", to: "/seller/products" },
        { label: "Склады", to: "/seller/inventory" },
        { label: "Импорт", to: "/seller/imports" },
        { label: "Отчёты", to: "/seller/reports" },
    ],
};

export function FooterBlock() {
    return (
        <footer className="bg-muted/30 border-t">
            <div className="container mx-auto max-w-6xl px-4 py-12">
                <div className="grid gap-8 sm:grid-cols-3">
                    {/* Brand */}
                    <div>
                        <Link to="/" className="flex items-center gap-2 text-lg font-bold">
                            <ShoppingCart className="size-6" />
                            Marketplace
                        </Link>
                        <p className="text-muted-foreground mt-3 text-sm">
                            Multi-Vendor Marketplace — платформа для продавцов и покупателей.
                        </p>
                        <p className="text-muted-foreground mt-6 text-xs">
                            © {new Date().getFullYear()} Marketplace. Все права защищены.
                        </p>
                    </div>

                    {/* Links */}
                    {Object.entries(FOOTER_LINKS).map(([title, links]) => (
                        <div key={title}>
                            <h4 className="mb-4 text-sm font-semibold">{title}</h4>
                            <ul className="space-y-2">
                                {links.map((link) => (
                                    <li key={link.to}>
                                        <Link
                                            to={link.to}
                                            className="text-muted-foreground hover:text-foreground text-sm transition-colors"
                                        >
                                            {link.label}
                                        </Link>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    ))}
                </div>

                <Separator className="my-8" />

                <div className="text-muted-foreground flex items-center justify-between text-xs">
                    <p>Сделано на React 19 + shadcn/ui + TanStack</p>
                    <div className="flex items-center gap-4">
                        <a href="#" className="hover:text-foreground">
                            Политика конфиденциальности
                        </a>
                        <a href="#" className="hover:text-foreground">
                            Условия использования
                        </a>
                    </div>
                </div>
            </div>
        </footer>
    );
}
