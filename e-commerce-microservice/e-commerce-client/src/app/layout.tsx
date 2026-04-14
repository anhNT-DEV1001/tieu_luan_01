import Chatbot from "@/components/chat/chatbot";
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Que Commerce Control Room",
  description:
    "Professional e-commerce dashboard built with Next.js and Tailwind CSS, connected to the gateway backend.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi" className="h-full antialiased">
      <body className="min-h-full flex flex-col bg-[var(--color-ink)] text-[var(--color-paper)] relative">
        {children}
        <Chatbot />
      </body>
    </html>
  );
}
