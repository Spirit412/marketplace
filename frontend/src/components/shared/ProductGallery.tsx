import useEmblaCarousel from "embla-carousel-react";
import Autoplay from "embla-carousel-autoplay";
import { useCallback, useEffect, useState } from "react";
import { ChevronLeft, ChevronRight, ImageOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ProductGalleryProps {
    images: string[];
    className?: string;
}

export function ProductGallery({ images, className }: ProductGalleryProps) {
    const [selected, set_selected] = useState(0);
    const [embla_ref, embla_api] = useEmblaCarousel({ loop: true }, [
        Autoplay({ delay: 5000, stopOnInteraction: true }),
    ]);

    const scroll_to = useCallback(
        (index: number) => {
            embla_api?.scrollTo(index);
            set_selected(index);
        },
        [embla_api],
    );

    const scroll_prev = useCallback(() => embla_api?.scrollPrev(), [embla_api]);
    const scroll_next = useCallback(() => embla_api?.scrollNext(), [embla_api]);

    useEffect(() => {
        if (!embla_api) return;
        const on_select = () => set_selected(embla_api.selectedScrollSnap());
        embla_api.on("select", on_select);
        return () => {
            embla_api.off("select", on_select);
        };
    }, [embla_api]);

    if (images.length === 0) {
        return (
            <div
                className={cn(
                    "bg-muted flex aspect-square items-center justify-center rounded-xl",
                    className,
                )}
            >
                <ImageOff className="text-muted-foreground size-16" />
            </div>
        );
    }

    return (
        <div className={cn("space-y-3", className)}>
            {/* Main carousel */}
            <div className="bg-muted relative overflow-hidden rounded-xl">
                <div ref={embla_ref} className="overflow-hidden">
                    <div className="flex">
                        {images.map((url, i) => (
                            <div key={i} className="aspect-square min-w-0 flex-[0_0_100%]">
                                <img
                                    src={url}
                                    alt=""
                                    className="h-full w-full object-cover"
                                    loading={i === 0 ? "eager" : "lazy"}
                                />
                            </div>
                        ))}
                    </div>
                </div>

                {images.length > 1 && (
                    <>
                        <Button
                            variant="ghost"
                            size="icon"
                            className="bg-background/80 hover:bg-background absolute top-1/2 left-2 -translate-y-1/2"
                            onClick={scroll_prev}
                        >
                            <ChevronLeft className="size-5" />
                        </Button>
                        <Button
                            variant="ghost"
                            size="icon"
                            className="bg-background/80 hover:bg-background absolute top-1/2 right-2 -translate-y-1/2"
                            onClick={scroll_next}
                        >
                            <ChevronRight className="size-5" />
                        </Button>
                    </>
                )}
            </div>

            {/* Thumbnails */}
            {images.length > 1 && (
                <div className="flex gap-2 overflow-x-auto pb-1">
                    {images.map((url, i) => (
                        <button
                            key={i}
                            onClick={() => scroll_to(i)}
                            className={cn(
                                "bg-muted size-16 shrink-0 overflow-hidden rounded-lg border-2 transition-colors",
                                i === selected
                                    ? "border-primary"
                                    : "hover:border-muted-foreground border-transparent",
                            )}
                        >
                            <img src={url} alt="" className="h-full w-full object-cover" />
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
}
