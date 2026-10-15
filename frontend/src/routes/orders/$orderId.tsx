import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { Check, Package, Truck } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { PriceTag } from "@/components/shared/PriceTag";
import { format_date } from "@/lib/utils";
import { getOrderFull } from "@/features/orders/order-service";
import type { OrderStatus } from "@/types";

const STATUS_STEPS: Array<{
    status: OrderStatus;
    label: string;
    icon: React.ComponentType<{ className?: string }>;
}> = [
    { status: "pending", label: "Создан", icon: Package },
    { status: "confirmed", label: "Подтверждён", icon: Check },
    { status: "shipped", label: "Отправлен", icon: Truck },
    { status: "delivered", label: "Доставлен", icon: Check },
];

export const Route = createFileRoute("/orders/$orderId")({
    component: OrderDetailPage,
});

function OrderDetailPage() {
    const { orderId } = Route.useParams();

    const {
        data: order,
        isLoading,
        isError,
    } = useQuery({
        queryKey: ["orders", orderId],
        queryFn: () => getOrderFull(orderId),
    });

    if (isLoading) return <DetailSkeleton />;
    if (isError || !order) {
        return <div className="text-muted-foreground py-8 text-center">Заказ не найден</div>;
    }

    const is_cancelled = order.status === "cancelled";
    const current_step = STATUS_STEPS.findIndex((s) => s.status === order.status);

    return (
        <div className="mx-auto max-w-3xl space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">
                        Заказ №{order.id.slice(0, 8)}…
                    </h1>
                    <p className="text-muted-foreground text-sm">{format_date(order.created_at)}</p>
                </div>
                <StatusBadge status={order.status as OrderStatus} />
            </div>

            {/* Status stepper */}
            {!is_cancelled && (
                <Card>
                    <CardContent className="py-6">
                        <div className="flex items-center justify-between">
                            {STATUS_STEPS.map((step, idx) => {
                                const Icon = step.icon;
                                const is_active = idx <= current_step;
                                const is_current = idx === current_step;
                                return (
                                    <div
                                        key={step.status}
                                        className="flex flex-1 flex-col items-center gap-2"
                                    >
                                        <div
                                            className={`flex size-10 items-center justify-center rounded-full border-2 ${
                                                is_active
                                                    ? "border-primary bg-primary text-primary-foreground"
                                                    : "border-muted-foreground/30 text-muted-foreground"
                                            } ${is_current ? "ring-primary ring-2 ring-offset-2" : ""}`}
                                        >
                                            <Icon className="size-5" />
                                        </div>
                                        <span className="text-muted-foreground text-center text-xs">
                                            {step.label}
                                        </span>
                                        {idx < STATUS_STEPS.length - 1 && (
                                            <div
                                                className={`absolute top-5 right-[calc(50%-2rem)] left-[calc(50%+2rem)] h-0.5 ${
                                                    idx < current_step ? "bg-primary" : "bg-muted"
                                                }`}
                                                style={{ left: "unset", right: "unset" }}
                                            />
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Order items */}
            <Card>
                <CardHeader>
                    <CardTitle className="text-lg">Состав заказа</CardTitle>
                </CardHeader>
                <CardContent className="divide-y">
                    {order.items.map((item) => (
                        <div
                            key={item.product_id}
                            className="flex items-center justify-between py-3"
                        >
                            <div>
                                <p className="font-medium">{item.product_name}</p>
                                <p className="text-muted-foreground text-sm">
                                    {item.quantity} × {item.price.toFixed(2)} ₽
                                </p>
                            </div>
                            <PriceTag price={item.price * item.quantity} size="sm" />
                        </div>
                    ))}
                </CardContent>
                <div className="border-t px-6 py-4">
                    <div className="flex justify-between text-lg font-bold">
                        <span>Итого</span>
                        <span>
                            {order.total.toFixed(2)} {order.currency}
                        </span>
                    </div>
                </div>
            </Card>

            {/* Payment info */}
            {order.payment && (
                <Card>
                    <CardHeader>
                        <CardTitle className="text-lg">Оплата</CardTitle>
                    </CardHeader>
                    <CardContent className="flex items-center justify-between">
                        <StatusBadge status={order.payment.status} />
                        <span className="font-medium">
                            {order.payment.amount.toFixed(2)} {order.payment.currency}
                        </span>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}

function DetailSkeleton() {
    return (
        <div className="mx-auto max-w-3xl space-y-6">
            <div className="flex justify-between">
                <div className="space-y-2">
                    <Skeleton className="h-8 w-48" />
                    <Skeleton className="h-4 w-32" />
                </div>
                <Skeleton className="h-6 w-24" />
            </div>
            <Skeleton className="h-40 w-full" />
            <Skeleton className="h-60 w-full" />
        </div>
    );
}
