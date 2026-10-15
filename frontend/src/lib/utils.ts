import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/** Объединяет CSS-классы с поддержкой Tailwind-конфликтов */
export function cn(...inputs: ClassValue[]): string {
    return twMerge(clsx(inputs));
}

/** Форматирует цену в рублях */
export function format_price(price: number, currency: string = "RUB"): string {
    return new Intl.NumberFormat("ru-RU", {
        style: "currency",
        currency,
        minimumFractionDigits: 2,
    }).format(price);
}

/** Форматирует дату в российском локале */
export function format_date(date: string | Date): string {
    return new Intl.DateTimeFormat("ru-RU", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    }).format(new Date(date));
}

/** Обрезает строку с многоточием */
export function truncate(text: string, max_length: number): string {
    if (text.length <= max_length) return text;
    return text.slice(0, max_length - 1) + "…";
}

import type { Category } from "@/types";

/** Строит дерево категорий из плоского списка по parent_id */
export function buildCategoryTree(flat: Category[]): Category[] {
    const map = new Map<string, Category & { children: Category[] }>();
    const roots: Category[] = [];

    for (const cat of flat) {
        map.set(cat.id, { ...cat, children: [] });
    }
    for (const cat of map.values()) {
        if (cat.parent_id && map.has(cat.parent_id)) {
            map.get(cat.parent_id)!.children.push(cat);
        } else {
            roots.push(cat);
        }
    }
    return roots;
}
