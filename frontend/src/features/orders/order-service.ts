import { api_client, order_client } from "@/lib/api-client";
import type { CartItem, Order, PaginatedResponse } from "@/types";

// ── Cart ──

export async function getCart(): Promise<CartItem[]> {
    const { data } = await order_client.get<{ items: CartItem[] }>("/cart/");
    return data.items;
}

export async function addToCart(product_id: string, quantity: number): Promise<void> {
    await order_client.post("/cart", { product_id, quantity });
}

export async function removeFromCart(product_id: string): Promise<void> {
    await order_client.delete(`/cart/${product_id}`);
}

// ── Orders ──

export interface OrderFilters {
    status?: string;
    page?: number;
    page_size?: number;
}

export async function getOrders(filters: OrderFilters = {}): Promise<PaginatedResponse<Order>> {
    const params = new URLSearchParams();
    if (filters.status) params.set("status", filters.status);
    if (filters.page) params.set("page", String(filters.page));
    if (filters.page_size) params.set("page_size", String(filters.page_size));

    const { data } = await order_client.get<{
        items: Order[];
        total_count: number;
        page: number;
        page_size: number;
    }>("/orders/", { params });
    return {
        items: data.items,
        total: data.total_count,
        page: data.page,
        page_size: data.page_size,
        pages: Math.ceil(data.total_count / data.page_size),
    };
}

interface PaymentSummary {
    id: string;
    status: string;
    amount: number;
    currency: string;
    gateway: string;
    gateway_payment_id: string | null;
}

export interface OrderFull extends Order {
    payment: PaymentSummary | null;
}

/** Заказ + статус оплаты (через api-service, составной эндпоинт) */
export async function getOrderFull(order_id: string): Promise<OrderFull> {
    const { data } = await api_client.get<OrderFull>(`/orders/${order_id}/full`);
    return data;
}

export interface CreateOrderData {
    address: string;
    payment_method: string;
    idempotency_key: string;
}

export async function createOrder(data: CreateOrderData): Promise<Order> {
    const response = await order_client.post<Order>("/orders", data);
    return response.data;
}

export async function cancelOrder(order_id: string): Promise<void> {
    await order_client.post(`/orders/${order_id}/cancel`);
}
