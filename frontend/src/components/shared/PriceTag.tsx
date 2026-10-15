import { format_price } from "@/lib/utils";

interface PriceTagProps {
    price: number;
    compare_at_price?: number | null;
    currency?: string;
    size?: "sm" | "md" | "lg";
}

export function PriceTag({
    price,
    compare_at_price,
    currency = "RUB",
    size = "md",
}: PriceTagProps) {
    const has_discount = compare_at_price && compare_at_price > price;
    const discount_pct = has_discount ? Math.round((1 - price / compare_at_price) * 100) : 0;

    const size_classes = {
        sm: "text-sm",
        md: "text-base",
        lg: "text-2xl",
    };

    return (
        <div className={`flex items-baseline gap-2 ${size_classes[size]}`}>
            <span className="text-foreground font-bold">{format_price(price, currency)}</span>
            {has_discount && compare_at_price && (
                <>
                    <span className="text-muted-foreground text-sm line-through">
                        {format_price(compare_at_price, currency)}
                    </span>
                    <span className="text-sm font-medium text-red-600 dark:text-red-400">
                        -{discount_pct}%
                    </span>
                </>
            )}
        </div>
    );
}
