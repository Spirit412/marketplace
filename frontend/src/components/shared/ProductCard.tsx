import { Link } from "@tanstack/react-router";
import { ImageOff, ShoppingCart } from "lucide-react";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { PriceTag } from "@/components/shared/PriceTag";
import { useDispatch } from "react-redux";
import { addItem } from "@/store/cart-slice";
import { toast } from "sonner";
import type { Product } from "@/types";
import { cn } from "@/lib/utils";

interface ProductCardProps {
    product: Product;
    className?: string;
}

export function ProductCard({ product, className }: ProductCardProps) {
    const dispatch = useDispatch();
    const image_url = Object.values(product.images)[0];
    const in_stock = product.stock > 0;

    const handleAddToCart = (e: React.MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();
        dispatch(
            addItem({
                product_id: product.id,
                name: product.name,
                price: product.price,
                quantity: 1,
                image_url: image_url ?? null,
            }),
        );
        toast.success("Добавлено в корзину");
    };

    return (
        <Link to="/products/$productId" params={{ productId: product.id }}>
            <Card className={cn("group h-full transition-shadow hover:shadow-md", className)}>
                {/* Image */}
                <div className="bg-muted relative aspect-square overflow-hidden rounded-t-xl">
                    {image_url ? (
                        <img
                            src={image_url}
                            alt={product.name}
                            className="h-full w-full object-cover transition-transform group-hover:scale-105"
                            loading="lazy"
                        />
                    ) : (
                        <div className="flex h-full items-center justify-center">
                            <ImageOff className="text-muted-foreground size-12" />
                        </div>
                    )}
                    {/* NOTE: compare_at_price removed — backend doesn't provide it */}
                </div>

                <CardContent className="p-3 pt-3">
                    <h3 className="line-clamp-2 text-sm leading-tight font-medium">
                        {product.name}
                    </h3>
                    <div className="mt-2">
                        <PriceTag
                            price={product.price}
                            size="sm"
                        />
                    </div>
                </CardContent>

                <CardFooter className="px-3 pt-0 pb-3">
                    {in_stock ? (
                        <Button
                            variant="outline"
                            size="sm"
                            className="w-full"
                            onClick={handleAddToCart}
                        >
                            <ShoppingCart className="mr-2 size-4" />В корзину
                        </Button>
                    ) : (
                        <Button variant="outline" size="sm" className="w-full" disabled>
                            Нет в наличии
                        </Button>
                    )}
                </CardFooter>
            </Card>
        </Link>
    );
}
