import { ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { Category } from "@/types";
import { useState } from "react";

interface CategoryTreeProps {
    categories: Category[];
    selected_id?: string | null;
    onSelect: (category_id: string | null) => void;
}

export function CategoryTree({ categories, selected_id, onSelect }: CategoryTreeProps) {
    return (
        <div className="space-y-1">
            <Button
                variant={!selected_id ? "secondary" : "ghost"}
                size="sm"
                className="w-full justify-start"
                onClick={() => onSelect(null)}
            >
                Все категории
            </Button>
            {categories.map((cat) => (
                <CategoryNode
                    key={cat.id}
                    category={cat}
                    depth={0}
                    selected_id={selected_id}
                    onSelect={onSelect}
                />
            ))}
        </div>
    );
}

function CategoryNode({
    category,
    depth,
    selected_id,
    onSelect,
}: {
    category: Category;
    depth: number;
    selected_id: string | null | undefined;
    onSelect: (id: string) => void;
}) {
    const [expanded, set_expanded] = useState(depth < 2); // авто-раскрытие до 2-го уровня
    const has_children = category.children.length > 0;
    const is_selected = selected_id === category.id;

    return (
        <div>
            <Button
                variant={is_selected ? "secondary" : "ghost"}
                size="sm"
                className={cn("w-full justify-start text-sm")}
                style={{ paddingLeft: `${12 + depth * 16}px` }}
                onClick={() => {
                    if (has_children) set_expanded((p) => !p);
                    onSelect(category.id);
                }}
            >
                {has_children && (
                    <ChevronRight
                        className={cn(
                            "mr-1 size-3 shrink-0 transition-transform",
                            expanded && "rotate-90",
                        )}
                    />
                )}
                <span className="truncate">{category.name}</span>
            </Button>
            {has_children && expanded && (
                <div>
                    {category.children.map((child) => (
                        <CategoryNode
                            key={child.id}
                            category={child}
                            depth={depth + 1}
                            selected_id={selected_id}
                            onSelect={onSelect}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}
