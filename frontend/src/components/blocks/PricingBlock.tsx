import { motion } from "framer-motion";
import { ArrowRight, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Link } from "@tanstack/react-router";

const PLANS = [
    {
        name: "Покупатель",
        price: "Бесплатно",
        description: "Всё для покупок",
        features: [
            "Просмотр каталога",
            "Корзина и заказы",
            "Отслеживание доставки",
            "Уведомления о статусе",
            "История покупок",
        ],
        cta: "Зарегистрироваться",
        to: "/register",
        popular: false,
    },
    {
        name: "Продавец",
        price: "Бесплатно",
        description: "Управление товарами и продажами",
        features: [
            "Неограниченное число товаров",
            "Управление складом",
            "Импорт CSV-прайсов",
            "Отчёты о продажах",
            "Интеграция с платёжными шлюзами",
        ],
        cta: "Стать продавцом",
        to: "/register",
        popular: true,
    },
];

export function PricingBlock() {
    return (
        <section className="py-16">
            <div className="container mx-auto max-w-6xl px-4">
                <div className="mx-auto max-w-2xl text-center">
                    <h2 className="text-3xl font-bold tracking-tight">Начните бесплатно</h2>
                    <p className="text-muted-foreground mt-4">
                        Выберите роль и начните пользоваться маркетплейсом без ограничений.
                    </p>
                </div>

                <div className="mt-12 grid gap-6 md:grid-cols-2">
                    {PLANS.map((plan, i) => (
                        <motion.div
                            key={i}
                            initial={{ opacity: 0, y: 30 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.4, delay: i * 0.15 }}
                            className={`bg-card relative flex flex-col rounded-2xl border p-8 ${
                                plan.popular ? "border-primary ring-primary shadow-lg ring-1" : ""
                            }`}
                        >
                            {plan.popular && (
                                <span className="bg-primary text-primary-foreground absolute -top-3 left-1/2 -translate-x-1/2 rounded-full px-4 py-1 text-xs font-medium">
                                    Популярное
                                </span>
                            )}
                            <h3 className="text-xl font-semibold">{plan.name}</h3>
                            <div className="mt-3">
                                <span className="text-3xl font-bold">{plan.price}</span>
                            </div>
                            <p className="text-muted-foreground mt-1 text-sm">{plan.description}</p>

                            <ul className="mt-8 flex-1 space-y-3">
                                {plan.features.map((feature) => (
                                    <li key={feature} className="flex items-start gap-3">
                                        <Check className="text-primary mt-0.5 size-4 shrink-0" />
                                        <span className="text-sm">{feature}</span>
                                    </li>
                                ))}
                            </ul>

                            <Link to={plan.to} className="mt-8">
                                <Button
                                    className="w-full"
                                    variant={plan.popular ? "default" : "outline"}
                                >
                                    {plan.cta}
                                    <ArrowRight className="ml-2 size-4" />
                                </Button>
                            </Link>
                        </motion.div>
                    ))}
                </div>
            </div>
        </section>
    );
}
