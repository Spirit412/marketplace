import { Search, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useEffect, useRef, useState } from "react";

interface SearchBarProps {
    value: string;
    onChange: (value: string) => void;
    placeholder?: string;
    className?: string;
}

export function SearchBar({
    value,
    onChange,
    placeholder = "Поиск товаров…",
    className = "",
}: SearchBarProps) {
    const [local, set_local] = useState(value);
    const timer_ref = useRef<NodeJS.Timeout>(undefined);

    const handleChange = (new_value: string) => {
        set_local(new_value);
        clearTimeout(timer_ref.current);
        timer_ref.current = setTimeout(() => {
            onChange(new_value);
        }, 300);
    };

    const handleClear = () => {
        set_local("");
        clearTimeout(timer_ref.current);
        onChange("");
    };

    // Cleanup on unmount
    useEffect(() => {
        return () => clearTimeout(timer_ref.current);
    }, []);

    return (
        <div className={`relative ${className}`}>
            <Search className="text-muted-foreground absolute top-1/2 left-3 size-4 -translate-y-1/2" />
            <Input
                value={local}
                onChange={(e) => handleChange(e.target.value)}
                placeholder={placeholder}
                className="pr-9 pl-9"
            />
            {local && (
                <Button
                    variant="ghost"
                    size="icon"
                    className="absolute top-0 right-0 h-full px-3 hover:bg-transparent"
                    onClick={handleClear}
                >
                    <X className="text-muted-foreground size-4" />
                </Button>
            )}
        </div>
    );
}
