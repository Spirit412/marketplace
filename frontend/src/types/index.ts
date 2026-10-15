// =============================================================================
// Общие типы, зеркалирующие backend-контракты
// =============================================================================

/** UUID v7 (time-sortable) */
export type UUID = string;

/** Пагинация */
export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    page_size: number;
    pages: number;
}

// ---------- Auth ----------

export type Role = "customer" | "seller" | "moderator" | "admin" | "super_admin";

export interface LoginRequest {
    email: string;
    password: string;
}

export interface RegisterRequest {
    email: string;
    password: string;
    role?: Role;
    timezone?: string;
}

export interface TokenPair {
    access_token: string;
    refresh_token: string;
}

export interface UserProfile {
    id: UUID;
    email: string;
    role: Role;
    is_admin: boolean;
    timezone: string;
    is_blocked: boolean;
}

// ---------- Catalog ----------

export interface Product {
    id: UUID;
    seller_id: UUID;
    category_id: UUID;
    name: string;
    description: string | null;
    price: number;
    sku: string | null;
    stock: number;
    rating: number;
    custom_properties_config: Record<string, unknown> | null;
    images: Record<string, string>;
    is_active: boolean;
    status: string;
    created_at: string;
    updated_at: string;
}

export interface Category {
    id: UUID;
    name: string;
    slug: string;
    parent_id: UUID | null;
    depth: number;
    image_url: string | null;
    is_active: boolean;
    children: Category[];
}

// ---------- Orders ----------

export type OrderStatus = "pending" | "confirmed" | "shipped" | "delivered" | "cancelled";

export interface CartItem {
    product_id: UUID;
    name: string;
    price: number;
    quantity: number;
    image_url: string | null;
}

export interface Order {
    id: UUID;
    user_id: UUID;
    status: OrderStatus;
    items: OrderItem[];
    subtotal: number;
    tax: number;
    discount: number;
    shipping: number;
    total: number;
    currency: string;
    payment_method: string;
    shipping_address: string;
    notes: string | null;
    idempotency_key: string;
    created_at: string;
    updated_at: string;
}

export interface OrderItem {
    id: number;
    product_id: UUID;
    product_name: string;
    price: number;
    quantity: number;
    seller_id: UUID;
}

// ---------- Inventory ----------

export interface Warehouse {
    id: UUID;
    name: string;
    address: string | null;
    is_active: boolean;
}

export interface Stock {
    product_id: UUID;
    warehouse_id: UUID;
    quantity: number;
    reserved: number;
}

// ---------- Payment ----------

export type PaymentStatus = "pending" | "processing" | "succeeded" | "failed" | "refunded";

export interface Payment {
    id: UUID;
    order_id: UUID;
    amount: number;
    currency: string;
    status: PaymentStatus;
    payment_method: string;
    created_at: string;
}

// ---------- Notification ----------

export interface Notification {
    id: UUID;
    user_id: UUID;
    type: string;
    title: string;
    body: string;
    is_read: boolean;
    created_at: string;
}

// ---------- Report ----------

export type ReportStatus = "pending" | "processing" | "completed" | "failed";

export interface Report {
    id: UUID;
    user_id: UUID;
    report_type: string;
    status: ReportStatus;
    file_url: string | null;
    created_at: string;
}

// ---------- Import ----------

export type ImportStatus = "pending" | "processing" | "completed" | "failed";

export interface ImportTask {
    id: UUID;
    seller_id: UUID;
    import_type: string;
    status: ImportStatus;
    errors: ImportError[];
    created_at: string;
}

export interface ImportError {
    row: number;
    field: string;
    message: string;
}
