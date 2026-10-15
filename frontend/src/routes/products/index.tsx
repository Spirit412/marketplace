import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { SearchBar } from "@/components/shared/SearchBar";
import { ProductCard } from "@/components/shared/ProductCard";
import { ProductGridSkeleton } from "@/components/shared/LoadingSkeleton";
import { EmptyState } from "@/components/shared/EmptyState";
import { CategoryTree } from "@/features/catalog/CategoryTree";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import {
    getCategories,
    getProducts,
    type ProductFilters,
} from "@/features/catalog/catalog-service";
import { ChevronLeft, ChevronRight, SlidersHorizontal } from "lucide-react";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";

const PAGE_SIZE = 24;

export const Route = createFileRoute("/products/")({
    component: ProductListPage,
    validateSearch: (search: Record<string, string>): ProductFilters => ({
        q: search.q,
        category_id: search.category_id,
        sort: search.sort as ProductFilters["sort"] | undefined,
        order: search.order as ProductFilters["order"] | undefined,
        page: search.page ? Number(search.page) : 1,
    }),
});

function ProductListPage() {
    const search = Route.useSearch();
    const navigate = Route.useNavigate();
    const [sidebar_open, set_sidebar_open] = useState(false);

    const filters: ProductFilters = {
        ...search,
        page_size: PAGE_SIZE,
    };

    const { data: categories } = useQuery({
        queryKey: ["categories"],
        queryFn: getCategories,
        staleTime: 5 * 60_000,
    });

    const { data, isLoading, isError, refetch } = useQuery({
        queryKey: ["products", filters],
        queryFn: () => getProducts(filters),
        placeholderData: (prev) => prev,
    });

    const updateFilters = (patch: Partial<ProductFilters>) => {
        void navigate({
            search: { ...search, ...patch, page: patch.page ?? 1 } as Record<string, string>,
        });
    };

    const total_pages = data ? Math.ceil(data.total / PAGE_SIZE) : 0;

    return (
        <div className="flex gap-6">
            {/* Filters sidebar — desktop */}
            <aside className="hidden w-56 shrink-0 lg:block">
                <div className="sticky top-20 space-y-6">
                    <div>
                        <h2 className="mb-3 text-sm font-semibold">Категории</h2>
                        {categories && (
                            <CategoryTree
                                categories={categories}
                                selected_id={search.category_id ?? null}
                                onSelect={(id) => updateFilters({ category_id: id ?? undefined })}
                            />
                        )}
                    </div>
                </div>
            </aside>

            {/* Mobile filter button */}
            <div className="fixed right-4 bottom-4 z-40 lg:hidden">
                <Sheet open={sidebar_open} onOpenChange={set_sidebar_open}>
                    <SheetTrigger asChild>
                        <Button size="icon" className="size-12 rounded-full shadow-lg">
                            <SlidersHorizontal className="size-5" />
                        </Button>
                    </SheetTrigger>
                    <SheetContent side="left" className="w-72">
                        <h2 className="mb-3 text-sm font-semibold">Категории</h2>
                        {categories && (
                            <CategoryTree
                                categories={categories}
                                selected_id={search.category_id ?? null}
                                onSelect={(id) => {
                                    updateFilters({ category_id: id ?? undefined });
                                    set_sidebar_open(false);
                                }}
                            />
                        )}
                    </SheetContent>
                </Sheet>
            </div>

            {/* Main */}
            <div className="min-w-0 flex-1 space-y-4">
                {/* Search + Sort */}
                <div className="flex flex-wrap items-center gap-3">
                    <SearchBar
                        value={search.q ?? ""}
                        onChange={(q) => updateFilters({ q: q || undefined })}
                        className="max-w-md min-w-[200px] flex-1"
                    />
                    <Select
                        value={search.sort ? `${search.sort}-${search.order ?? "desc"}` : ""}
                        onValueChange={(val) => {
                            const [sort, order] = val.split("-");
                            updateFilters({
                                sort: sort as ProductFilters["sort"],
                                order: order as ProductFilters["order"],
                            });
                        }}
                    >
                        <SelectTrigger className="w-[180px]">
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="created_at-desc">Новые сначала</SelectItem>
                            <SelectItem value="created_at-asc">Старые сначала</SelectItem>
                            <SelectItem value="price-asc">Цена: по возрастанию</SelectItem>
                            <SelectItem value="price-desc">Цена: по убыванию</SelectItem>
                            <SelectItem value="name-asc">Название: А-Я</SelectItem>
                        </SelectContent>
                    </Select>
                </div>

                {/* Results */}
                {isLoading ? (
                    <ProductGridSkeleton />
                ) : isError ? (
                    <div className="flex flex-col items-center gap-3 py-16">
                        <p className="text-muted-foreground">Ошибка загрузки каталога</p>
                        <Button
                            variant="outline"
                            onClick={() => {
                                void refetch();
                            }}
                        >
                            Повторить
                        </Button>
                    </div>
                ) : !data || data.items.length === 0 ? (
                    <EmptyState
                        title="Товаров не найдено"
                        description={
                            search.q || search.category_id
                                ? "Попробуйте изменить параметры поиска"
                                : "В каталоге пока нет товаров"
                        }
                        {...(search.q || search.category_id
                            ? {
                                  action_label: "Сбросить фильтры",
                                  action_to: ".",
                              }
                            : {})}
                    />
                ) : (
                    <>
                        <p className="text-muted-foreground text-sm">Найдено: {data.total}</p>
                        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
                            {data.items.map((product) => (
                                <ProductCard key={product.id} product={product} />
                            ))}
                        </div>

                        {/* Pagination */}
                        {total_pages > 1 && (
                            <div className="flex items-center justify-center gap-2 pt-4">
                                <Button
                                    variant="outline"
                                    size="sm"
                                    disabled={!search.page || search.page <= 1}
                                    onClick={() => updateFilters({ page: (search.page ?? 1) - 1 })}
                                >
                                    <ChevronLeft className="size-4" />
                                </Button>
                                <span className="text-muted-foreground text-sm">
                                    {search.page ?? 1} / {total_pages}
                                </span>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    disabled={(search.page ?? 1) >= total_pages}
                                    onClick={() => updateFilters({ page: (search.page ?? 1) + 1 })}
                                >
                                    <ChevronRight className="size-4" />
                                </Button>
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
}
