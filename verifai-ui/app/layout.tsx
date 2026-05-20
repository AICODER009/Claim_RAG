import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/Sidebar";
import { ThemeProvider } from "@/components/ThemeProvider";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  weight: ["300", "400", "500", "600", "700", "800"],
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains",
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: "Revisto — Claim Substantiation",
  description:
    "Life Sciences Marketing Compliance, powered by AI. Accelerate claim substantiation while ensuring quality and regulatory compliance.",
  icons: [
    { rel: "icon", url: "/icon.png", type: "image/png" },
    { rel: "shortcut icon", url: "/icon.png", type: "image/png" },
    { rel: "apple-touch-icon", url: "/icon.png" },
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${inter.variable} ${jetbrainsMono.variable}`}
        style={{ fontFamily: "var(--font-inter, 'Inter', sans-serif)" }}
      >
        <ThemeProvider>
          <div style={{ display: "flex", height: "100vh", overflow: "hidden" }}>
            <Sidebar />
            <main
              style={{
                flex: 1,
                overflowY: "auto",
                background: "var(--bg-primary)",
                height: "100%",
              }}
            >
              {children}
            </main>
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
