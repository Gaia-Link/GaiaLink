import { Web3Provider } from "@/providers/Web3Provider";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Gaia Link - App",
  description: "Interactive Humanitarian Aid Map",
};

export default function AppLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <Web3Provider>
      {children}
    </Web3Provider>
  );
}
