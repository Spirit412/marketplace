import type { ReactNode } from "react";
import { FooterBlock } from "@/components/blocks/FooterBlock";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";

export function AppLayout({ children }: { children: ReactNode }) {
    return (
        <div className="flex min-h-screen flex-col">
            <Header />
            <div className="flex flex-1">
                <Sidebar />
                <main className="bg-muted/30 flex-1 overflow-auto p-4 md:p-6">{children}</main>
            </div>
            <FooterBlock />
        </div>
    );
}
