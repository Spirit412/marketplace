import { useDispatch, useSelector } from "react-redux";
import { Link } from "@tanstack/react-router";
import { ImageOff, Minus, Plus, ShoppingCart, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
    Sheet,
    SheetContent,
    SheetFooter,
    SheetHeader,
    SheetTitle,
    SheetTrigger,
} from "@/components/ui/sheet";
import { PriceTag } from "@/components/shared/PriceTag";
import {
    removeItem,
    selectCartCount,
    selectCartItems,
    selectCartTotal,
    updateQuantity,
} from "@/store/cart-slice";

export function CartDrawer() {
    const dispatch = useDispatch();
    const items = useSelector(selectCartItems);
    const total = useSelector(selectCartTotal);
    const count = useSelector(selectCartCount);

    return (
        <Sheet>
            <SheetTrigger asChild>
                <Button variant="ghost" size="icon" className="relative">
                    <ShoppingCart className="size-5" />
                    {count > 0 && (
                        <span className="bg-primary text-primary-foreground absolute -top-1 -right-1 flex size-5 items-center justify-center rounded-full text-[10px] font-bold">
                            {count > 99 ? "99+" : count}
                        </span>
                    )}
                </Button>
            </SheetTrigger>
            <SheetContent className="flex w-full flex-col sm:max-w-md">
                <SheetHeader className="text-left">
                    <SheetTitle>Корзина ({count})</SheetTitle>
                </SheetHeader>

                {items.length === 0 ? (
                    <div className="text-muted-foreground flex flex-1 flex-col items-center justify-center gap-4">
                        <ShoppingCart className="size-16" />
                        <p className="text-lg font-medium">Корзина пуста</p>
                        <p className="text-sm">Добавьте товары из каталога</p>
                    </div>
                ) : (
                    <>
                        <ScrollArea className="-mx-6 flex-1 px-6">
                            <div className="space-y-4">
                                {items.map((item) => (
                                    <div key={item.product_id} className="flex gap-4">
                                        <div className="bg-muted size-20 shrink-0 overflow-hidden rounded-lg">
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
                                        <div className="flex flex-1 flex-col justify-between">
                                            <div>
                                                <Link
                                                    to="/products/$productId"
                                                    params={{ productId: item.product_id }}
                                                    className="line-clamp-1 text-sm font-medium hover:underline"
                                                >
                                                    {item.name}
                                                </Link>
                                                <PriceTag price={item.price} size="sm" />
                                            </div>
                                            <div className="flex items-center justify-between">
                                                <div className="flex items-center gap-1 rounded-md border">
                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        className="size-7"
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
                                                    <span className="w-7 text-center text-xs tabular-nums">
                                                        {item.quantity}
                                                    </span>
                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        className="size-7"
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
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    className="text-muted-foreground hover:text-destructive size-7"
                                                    onClick={() =>
                                                        dispatch(removeItem(item.product_id))
                                                    }
                                                >
                                                    <Trash2 className="size-4" />
                                                </Button>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </ScrollArea>

                        <Separator className="my-0" />
                        <SheetFooter className="flex-col gap-4 sm:flex-col">
                            <div className="flex items-center justify-between">
                                <span className="text-muted-foreground text-sm">Итого</span>
                                <span className="text-xl font-bold">{total.toFixed(2)} ₽</span>
                            </div>
                            <Link to="/orders" className="w-full">
                                <Button className="w-full" size="lg">
                                    Оформить заказ
                                </Button>
                            </Link>
                        </SheetFooter>
                    </>
                )}
            </SheetContent>
        </Sheet>
    );
}
