import { motion } from "framer-motion";
import { ArrowRight, Package, Shield, ShoppingCart, Truck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Link } from "@tanstack/react-router";

const FEATURES = [
    {
        icon: Package,
        title: "Тысячи товаров",
        description: "Каталог от проверенных продавцов с доставкой по всей стране.",
    },
    {
        icon: ShoppingCart,
        title: "Удобная корзина",
        description: "Добавляйте товары в один клик, меняйте количество перед заказом.",
    },
    {
        icon: Truck,
        title: "Быстрая доставка",
        description: "Отслеживайте статус заказа в реальном времени от оформления до двери.",
    },
    {
        icon: Shield,
        title: "Безопасные платежи",
        description: "Оплата через проверенные платёжные шлюзы с защитой покупателя.",
    },
];

export function HeroBlock() {
    return (
        <section className="relative overflow-hidden py-16 md:py-24">
            {/* Background gradient */}
            <div className="from-primary/5 via-background to-accent/10 pointer-events-none absolute inset-0 bg-gradient-to-br" />

            <div className="relative container mx-auto max-w-6xl px-4">
                <div className="mx-auto max-w-3xl text-center">
                    <motion.h1
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5 }}
                        className="text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl"
                    >
                        Маркетплейс для
                        <span className="text-primary"> продавцов </span>и покупателей
                    </motion.h1>

                    <motion.p
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5, delay: 0.1 }}
                        className="text-muted-foreground mt-6 text-lg md:text-xl"
                    >
                        Продавайте товары, управляйте складом, принимайте платежи. Или покупайте —
                        тысячи товаров с доставкой.
                    </motion.p>

                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5, delay: 0.2 }}
                        className="mt-8 flex flex-wrap items-center justify-center gap-4"
                    >
                        <Link to="/products">
                            <Button size="lg" className="text-base">
                                Смотреть каталог
                                <ArrowRight className="ml-2 size-5" />
                            </Button>
                        </Link>
                        <Link to="/register">
                            <Button variant="outline" size="lg" className="text-base">
                                Стать продавцом
                            </Button>
                        </Link>
                    </motion.div>
                </div>

                {/* Feature cards */}
                <motion.div
                    initial={{ opacity: 0, y: 40 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.3 }}
                    className="mt-20 grid gap-6 sm:grid-cols-2 lg:grid-cols-4"
                >
                    {FEATURES.map((feature, i) => (
                        <div
                            key={i}
                            className="group bg-card rounded-xl border p-6 transition-shadow hover:shadow-lg"
                        >
                            <div className="bg-primary/10 mb-4 flex size-10 items-center justify-center rounded-lg">
                                <feature.icon className="text-primary size-5" />
                            </div>
                            <h3 className="mb-2 font-semibold">{feature.title}</h3>
                            <p className="text-muted-foreground text-sm">{feature.description}</p>
                        </div>
                    ))}
                </motion.div>
            </div>
        </section>
    );
}
