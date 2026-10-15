import { type LucideIcon, Package } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Link } from "@tanstack/react-router";

interface EmptyStateProps {
    icon?: LucideIcon;
    title: string;
    description?: string;
    action_label?: string;
    action_to?: string;
}

export function EmptyState({
    icon: Icon = Package,
    title,
    description,
    action_label,
    action_to,
}: EmptyStateProps) {
    return (
        <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
            <div className="bg-muted flex size-16 items-center justify-center rounded-full">
                <Icon className="text-muted-foreground size-8" />
            </div>
            <p className="text-lg font-medium">{title}</p>
            {description && <p className="text-muted-foreground max-w-sm text-sm">{description}</p>}
            {action_label && action_to && (
                <Link to={action_to}>
                    <Button variant="outline" className="mt-2">
                        {action_label}
                    </Button>
                </Link>
            )}
        </div>
    );
}
