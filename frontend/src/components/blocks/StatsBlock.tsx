import { motion } from "framer-motion";
import { BarChart3, Package, ShoppingCart, Users } from "lucide-react";

interface StatsBlockProps {
    products_count?: number;
    orders_count?: number;
    sellers_count?: number;
    customers_count?: number;
}

export function StatsBlock({
    products_count = 0,
    orders_count = 0,
    sellers_count = 0,
    customers_count = 0,
}: StatsBlockProps) {
    const stats = [
        { icon: Package, value: products_count, label: "Товаров" },
        { icon: ShoppingCart, value: orders_count, label: "Заказов" },
        { icon: Users, value: sellers_count, label: "Продавцов" },
        { icon: BarChart3, value: customers_count, label: "Покупателей" },
    ];

    return (
        <section className="py-16">
            <div className="container mx-auto max-w-6xl px-4">
                <div className="grid grid-cols-2 gap-6 md:grid-cols-4">
                    {stats.map((stat, i) => (
                        <motion.div
                            key={i}
                            initial={{ opacity: 0, scale: 0.9 }}
                            whileInView={{ opacity: 1, scale: 1 }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.3, delay: i * 0.1 }}
                            className="bg-card flex flex-col items-center gap-2 rounded-xl border p-6"
                        >
                            <stat.icon className="text-primary size-6" />
                            <span className="text-3xl font-bold tabular-nums">
                                {stat.value.toLocaleString("ru-RU")}
                            </span>
                            <span className="text-muted-foreground text-sm">{stat.label}</span>
                        </motion.div>
                    ))}
                </div>
            </div>
        </section>
    );
}
