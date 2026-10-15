import { Skeleton } from "@/components/ui/skeleton";

/** Card skeleton for product grids */
export function ProductCardSkeleton() {
    return (
        <div className="space-y-2">
            <Skeleton className="aspect-square rounded-xl" />
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
            <Skeleton className="h-8 w-full rounded-md" />
        </div>
    );
}

/** Grid of N skeleton cards */
export function ProductGridSkeleton({ count = 8 }: { count?: number }) {
    return (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
            {Array.from({ length: count }).map((_, i) => (
                <ProductCardSkeleton key={i} />
            ))}
        </div>
    );
}

/** Table rows skeleton */
export function TableSkeleton({ rows = 5, cols = 4 }: { rows?: number; cols?: number }) {
    return (
        <div className="space-y-1">
            {Array.from({ length: rows }).map((_, i) => (
                <div key={i} className="flex gap-4 py-3">
                    {Array.from({ length: cols }).map((_, j) => (
                        <Skeleton key={j} className="h-8 flex-1" />
                    ))}
                </div>
            ))}
        </div>
    );
}

/** Full detail page skeleton */
export function DetailSkeleton() {
    return (
        <div className="mx-auto max-w-5xl">
            <Skeleton className="mb-4 h-4 w-32" />
            <div className="grid gap-8 lg:grid-cols-2">
                <Skeleton className="aspect-square rounded-xl" />
                <div className="space-y-4">
                    <Skeleton className="h-8 w-3/4" />
                    <Skeleton className="h-6 w-1/3" />
                    <Skeleton className="h-4 w-1/4" />
                    <Skeleton className="h-32 w-full" />
                    <Skeleton className="h-10 w-40" />
                </div>
            </div>
        </div>
    );
}
