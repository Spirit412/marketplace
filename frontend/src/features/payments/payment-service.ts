import { payment_client } from "@/lib/api-client";
import type { Payment } from "@/types";

export async function getPaymentByOrder(order_id: string): Promise<Payment> {
    const { data } = await payment_client.get<Payment>(`/payments/by-order/${order_id}`);
    return data;
}
