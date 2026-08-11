import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Cartes NDVI Bénin",
  description: "Cartes eVIIRS 375 m du Bénin, FEWS NET",
  icons: { icon: "/icon.svg" },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="fr"><body>{children}</body></html>;
}
