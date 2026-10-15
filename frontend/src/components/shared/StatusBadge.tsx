import { Badge } from "@/components/ui/badge";
import type { OrderStatus, PaymentStatus } from "@/types";

const STATUS_STYLES: Record<string, string> = {
    // Orders
    pending: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
    confirmed: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
    shipped: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200",
    delivered: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
    cancelled: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
    // Payments
    processing: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
    succeeded: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
    failed: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
    refunded: "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200",
};

const STATUS_LABELS: Record<string, string> = {
    pending: "Ожидает",
    confirmed: "Подтверждён",
    shipped: "Отправлен",
    delivered: "Доставлен",
    cancelled: "Отменён",
    processing: "Обрабатывается",
    succeeded: "Оплачен",
    failed: "Ошибка",
    refunded: "Возврат",
};

interface StatusBadgeProps {
    status: OrderStatus | PaymentStatus | string;
}

export function StatusBadge({ status }: StatusBadgeProps) {
    const style = STATUS_STYLES[status] ?? "bg-gray-100 text-gray-800";
    const label = STATUS_LABELS[status] ?? status;

    return (
        <Badge className={style} variant="outline">
            {label}
        </Badge>
    );
}
