import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { ChevronLeft, ChevronRight, ImageOff, ShoppingCart } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { PriceTag } from "@/components/shared/PriceTag";
import { cn } from "@/lib/utils";
import { getProduct } from "@/features/catalog/catalog-service";
import { useDispatch } from "react-redux";
import { addItem } from "@/store/cart-slice";
import { toast } from "sonner";

export const Route = createFileRoute("/products/$productId")({
    component: ProductDetailPage,
});

function ProductDetailPage() {
    const { productId } = Route.useParams();
    const dispatch = useDispatch();
    const [quantity, set_quantity] = useState(1);
    const [active_image, set_active_image] = useState(0);

    const {
        data: product,
        isLoading,
        isError,
    } = useQuery({
        queryKey: ["products", productId],
        queryFn: () => getProduct(productId),
    });

    if (isLoading) return <DetailSkeleton />;
    if (isError || !product) {
        return (
            <div className="flex flex-col items-center gap-3 py-16">
                <p className="text-muted-foreground">Товар не найден</p>
            </div>
        );
    }

    const images: string[] = Object.values(product.images);
    const in_stock = product.stock > 0;

    const handleAddToCart = () => {
        dispatch(
            addItem({
                product_id: product.id,
                name: product.name,
                price: product.price,
                quantity,
                image_url: images[0] ?? null,
            }),
        );
        toast.success(`Добавлено в корзину: ${product.name}`);
    };

    return (
        <div className="mx-auto max-w-5xl">
            {/* Breadcrumbs */}
            <p className="text-muted-foreground mb-4 text-sm">Каталог / {product.name}</p>

            <div className="grid gap-8 lg:grid-cols-2">
                {/* Gallery */}
                <div className="space-y-3">
                    <div className="bg-muted relative aspect-square overflow-hidden rounded-xl">
                        {images[active_image] ? (
                            <img
                                src={images[active_image]}
                                alt={product.name}
                                className="h-full w-full object-cover"
                            />
                        ) : (
                            <div className="flex h-full items-center justify-center">
                                <ImageOff className="text-muted-foreground size-20" />
                            </div>
                        )}
                        {images.length > 1 && (
                            <>
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="bg-background/80 absolute top-1/2 left-2 -translate-y-1/2"
                                    onClick={() =>
                                        set_active_image(
                                            (prev) => (prev - 1 + images.length) % images.length,
                                        )
                                    }
                                >
                                    <ChevronLeft className="size-5" />
                                </Button>
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="bg-background/80 absolute top-1/2 right-2 -translate-y-1/2"
                                    onClick={() =>
                                        set_active_image((prev) => (prev + 1) % images.length)
                                    }
                                >
                                    <ChevronRight className="size-5" />
                                </Button>
                            </>
                        )}
                    </div>
                    {/* Thumbnails */}
                    {images.length > 1 && (
                        <div className="flex gap-2 overflow-x-auto pb-1">
                            {images.map((url, idx) => (
                                <button
                                    key={idx}
                                    onClick={() => set_active_image(idx)}
                                    className={cn(
                                        "bg-muted size-16 shrink-0 overflow-hidden rounded-lg border-2",
                                        idx === active_image
                                            ? "border-primary"
                                            : "border-transparent",
                                    )}
                                >
                                    <img src={url} alt="" className="h-full w-full object-cover" />
                                </button>
                            ))}
                        </div>
                    )}
                </div>

                {/* Info */}
                <div className="space-y-6">
                    <div>
                        <h1 className="text-2xl font-bold tracking-tight">{product.name}</h1>
                        <div className="mt-3">
                            <PriceTag price={product.price} size="lg" />
                        </div>
                    </div>

                    {/* Stock */}
                    <div className="flex items-center gap-2">
                        <Badge variant={in_stock ? "default" : "destructive"}>
                            {in_stock ? `В наличии: ${product.stock} шт.` : "Нет в наличии"}
                        </Badge>
                    </div>

                    {/* Dynamic properties */}
                    {product.custom_properties_config && Object.keys(product.custom_properties_config).length > 0 && (
                        <div className="rounded-lg border">
                            <table className="w-full text-sm">
                                <tbody>
                                    {Object.entries(product.custom_properties_config).map(
                                        ([key, value]) => (
                                            <tr key={key} className="border-b last:border-0">
                                                <td className="text-muted-foreground w-1/3 px-4 py-2 font-medium">
                                                    {key}
                                                </td>
                                                <td className="px-4 py-2">{String(value)}</td>
                                            </tr>
                                        ),
                                    )}
                                </tbody>
                            </table>
                        </div>
                    )}

                    {/* Description */}
                    {product.description && (
                        <div>
                            <h2 className="mb-2 text-sm font-semibold">Описание</h2>
                            <p className="text-muted-foreground text-sm whitespace-pre-wrap">
                                {product.description}
                            </p>
                        </div>
                    )}

                    {/* Add to cart */}
                    {in_stock && (
                        <div className="flex items-center gap-3">
                            <div className="flex items-center rounded-lg border">
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    disabled={quantity <= 1}
                                    onClick={() => set_quantity((q) => Math.max(1, q - 1))}
                                >
                                    -
                                </Button>
                                <span className="w-10 text-center text-sm tabular-nums">
                                    {quantity}
                                </span>
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    disabled={quantity >= product.stock}
                                    onClick={() =>
                                        set_quantity((q) => Math.min(product.stock, q + 1))
                                    }
                                >
                                    +
                                </Button>
                            </div>
                            <Button size="lg" onClick={handleAddToCart}>
                                <ShoppingCart className="mr-2 size-5" />В корзину
                            </Button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

function DetailSkeleton() {
    return (
        <div className="mx-auto max-w-5xl">
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
