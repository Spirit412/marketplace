import { createFileRoute, Link } from "@tanstack/react-router";
import { useDispatch, useSelector } from "react-redux";
import { ImageOff, Minus, Plus, ShoppingCart, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { PriceTag } from "@/components/shared/PriceTag";
import {
    clearCart,
    removeItem,
    selectCartCount,
    selectCartItems,
    selectCartTotal,
    updateQuantity,
} from "@/store/cart-slice";

export const Route = createFileRoute("/cart")({
    component: CartPage,
});

function CartPage() {
    const dispatch = useDispatch();
    const items = useSelector(selectCartItems);
    const total = useSelector(selectCartTotal);
    const count = useSelector(selectCartCount);

    if (items.length === 0) {
        return (
            <div className="flex flex-col items-center gap-4 py-16">
                <ShoppingCart className="text-muted-foreground size-16" />
                <p className="text-lg font-medium">Корзина пуста</p>
                <p className="text-muted-foreground text-sm">Добавьте товары из каталога</p>
                <Link to="/products">
                    <Button>Перейти в каталог</Button>
                </Link>
            </div>
        );
    }

    return (
        <div className="mx-auto max-w-3xl space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-bold tracking-tight">Корзина ({count})</h1>
                <Button variant="ghost" size="sm" onClick={() => dispatch(clearCart())}>
                    <Trash2 className="mr-2 size-4" />
                    Очистить
                </Button>
            </div>

            <Card>
                <CardHeader className="sr-only">
                    <CardTitle>Товары в корзине</CardTitle>
                </CardHeader>
                <ScrollArea className="max-h-[60vh]">
                    <CardContent className="divide-y p-0">
                        {items.map((item) => (
                            <div key={item.product_id} className="flex items-center gap-4 p-4">
                                {/* Image */}
                                <div className="bg-muted size-16 shrink-0 overflow-hidden rounded-lg">
                                    {item.image_url ? (
                                        <img
                                            src={item.image_url}
                                            alt={item.name}
                                            className="h-full w-full object-cover"
                                        />
                                    ) : (
                                        <div className="flex h-full items-center justify-center">
                                            <ImageOff className="text-muted-foreground size-6" />
                                        </div>
                                    )}
                                </div>

                                {/* Info */}
                                <div className="min-w-0 flex-1">
                                    <Link
                                        to="/products/$productId"
                                        params={{ productId: item.product_id }}
                                        className="line-clamp-1 text-sm font-medium hover:underline"
                                    >
                                        {item.name}
                                    </Link>
                                    <PriceTag price={item.price} size="sm" />
                                </div>

                                {/* Quantity controls */}
                                <div className="flex items-center gap-1 rounded-lg border">
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        className="size-8"
                                        onClick={() =>
                                            dispatch(
                                                updateQuantity({
                                                    product_id: item.product_id,
                                                    quantity: item.quantity - 1,
                                                }),
                                            )
                                        }
                                    >
                                        <Minus className="size-3" />
                                    </Button>
                                    <span className="w-8 text-center text-sm tabular-nums">
                                        {item.quantity}
                                    </span>
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        className="size-8"
                                        onClick={() =>
                                            dispatch(
                                                updateQuantity({
                                                    product_id: item.product_id,
                                                    quantity: item.quantity + 1,
                                                }),
                                            )
                                        }
                                    >
                                        <Plus className="size-3" />
                                    </Button>
                                </div>

                                {/* Remove */}
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="text-muted-foreground hover:text-destructive size-8"
                                    onClick={() => dispatch(removeItem(item.product_id))}
                                >
                                    <Trash2 className="size-4" />
                                </Button>
                            </div>
                        ))}
                    </CardContent>
                </ScrollArea>

                <Separator />

                <CardFooter className="flex items-center justify-between p-4">
                    <div>
                        <p className="text-muted-foreground text-sm">Итого</p>
                        <p className="text-xl font-bold">{total.toFixed(2)} ₽</p>
                    </div>
                    <Link to="/orders">
                        <Button size="lg">Оформить заказ</Button>
                    </Link>
                </CardFooter>
            </Card>
        </div>
    );
}
