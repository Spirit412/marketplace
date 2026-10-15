import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Eye } from "lucide-react";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { format_date } from "@/lib/utils";
import { getOrders } from "@/features/orders/order-service";
import type { OrderStatus } from "@/types";

const STATUS_TABS: Array<{ value: string; label: string }> = [
    { value: "", label: "Все" },
    { value: "pending", label: "Активные" },
    { value: "delivered", label: "Завершённые" },
    { value: "cancelled", label: "Отменённые" },
];

export const Route = createFileRoute("/orders/")({
    component: OrderListPage,
});

function OrderListPage() {
    const [status, set_status] = useState("");
    const [page, set_page] = useState(1);

    const { data, isLoading, isError } = useQuery({
        queryKey: ["orders", { status: status || undefined, page }],
        queryFn: () => getOrders({ status: status || undefined, page }),
    });

    return (
        <div className="space-y-6">
            <h1 className="text-2xl font-bold tracking-tight">Мои заказы</h1>

            <Tabs
                value={status}
                onValueChange={(v) => {
                    set_status(v);
                    set_page(1);
                }}
            >
                <TabsList>
                    {STATUS_TABS.map((tab) => (
                        <TabsTrigger key={tab.value} value={tab.value}>
                            {tab.label}
                        </TabsTrigger>
                    ))}
                </TabsList>
            </Tabs>

            {isLoading ? (
                <div className="space-y-2">
                    {Array.from({ length: 5 }).map((_, i) => (
                        <Skeleton key={i} className="h-12 w-full" />
                    ))}
                </div>
            ) : isError ? (
                <p className="text-muted-foreground py-8 text-center">Ошибка загрузки заказов</p>
            ) : !data || data.items.length === 0 ? (
                <p className="text-muted-foreground py-8 text-center">Заказов не найдено</p>
            ) : (
                <>
                    <div className="rounded-md border">
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>№ заказа</TableHead>
                                    <TableHead>Дата</TableHead>
                                    <TableHead>Сумма</TableHead>
                                    <TableHead>Статус</TableHead>
                                    <TableHead className="w-16" />
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {data.items.map((order) => (
                                    <TableRow key={order.id}>
                                        <TableCell className="font-mono text-xs">
                                            {order.id.slice(0, 8)}…
                                        </TableCell>
                                        <TableCell className="text-sm">
                                            {format_date(order.created_at)}
                                        </TableCell>
                                        <TableCell className="font-medium">
                                            {order.total.toFixed(2)} {order.currency}
                                        </TableCell>
                                        <TableCell>
                                            <StatusBadge status={order.status as OrderStatus} />
                                        </TableCell>
                                        <TableCell>
                                            <Link
                                                to="/orders/$orderId"
                                                params={{ orderId: order.id }}
                                            >
                                                <Button variant="ghost" size="icon">
                                                    <Eye className="size-4" />
                                                </Button>
                                            </Link>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </div>

                    {/* Pagination */}
                    {data.pages > 1 && (
                        <div className="flex items-center justify-center gap-2">
                            <Button
                                variant="outline"
                                size="sm"
                                disabled={page <= 1}
                                onClick={() => set_page((p) => p - 1)}
                            >
                                Назад
                            </Button>
                            <span className="text-muted-foreground text-sm">
                                {page} / {data.pages}
                            </span>
                            <Button
                                variant="outline"
                                size="sm"
                                disabled={page >= data.pages}
                                onClick={() => set_page((p) => p + 1)}
                            >
                                Вперёд
                            </Button>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}
