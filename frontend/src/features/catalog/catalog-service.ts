import { api_client, catalog_client } from "@/lib/api-client";
import { buildCategoryTree } from "@/lib/utils";
import type { Category, PaginatedResponse, Product } from "@/types";

export interface ProductFilters {
    q?: string;
    category_id?: string;
    price__gte?: number;
    price__lte?: number;
    sort?: "price" | "created_at" | "name";
    order?: "asc" | "desc";
    page?: number;
    page_size?: number;
}

/** Список товаров с фильтрацией (напрямую к catalog-service) */
export async function getProducts(
    filters: ProductFilters = {},
): Promise<PaginatedResponse<Product>> {
    const params = new URLSearchParams();
    if (filters.q) params.set("q", filters.q);
    if (filters.category_id) params.set("category_id", filters.category_id);
    if (filters.price__gte !== undefined) params.set("price__gte", String(filters.price__gte));
    if (filters.price__lte !== undefined) params.set("price__lte", String(filters.price__lte));
    if (filters.sort) params.set("sort", filters.sort);
    if (filters.order) params.set("order", filters.order);
    if (filters.page) params.set("page", String(filters.page));
    if (filters.page_size) params.set("page_size", String(filters.page_size));

    const { data } = await catalog_client.get<PaginatedResponse<Product>>("/products/", { params });
    return data;
}

/** Карточка товара через api-service (составной: каталог + остаток) */
export async function getProduct(product_id: string): Promise<Product> {
    const { data } = await api_client.get<Product>(`/storefront/products/${product_id}`);
    return data;
}

/** Дерево категорий (напрямую к catalog-service) */
export async function getCategories(): Promise<Category[]> {
    const { data } = await catalog_client.get<{ items: Category[] }>("/categories/");
    return buildCategoryTree(data.items);
}

/** Создать товар (seller) */
export async function createProduct(data: FormData): Promise<Product> {
    const response = await catalog_client.post<Product>("/products", data, {
        headers: { "Content-Type": "multipart/form-data" },
    });
    return response.data;
}

/** Обновить товар (seller) */
export async function updateProduct(product_id: string, data: FormData): Promise<Product> {
    const response = await catalog_client.put<Product>(`/products/${product_id}`, data, {
        headers: { "Content-Type": "multipart/form-data" },
    });
    return response.data;
}

/** Удалить товар (soft delete) */
export async function deleteProduct(product_id: string): Promise<void> {
    await catalog_client.delete(`/products/${product_id}`);
}
