import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin", "vietnamese"],
  weight: ["400", "500", "600", "700", "800", "900"],
});

export const metadata = {
  title: "FreshRoute",
  description: "Food rescue & AI combo app",
};

export default function RootLayout({ children }) {
  return (
    <html lang="vi" className="h-full antialiased">
      <body
        suppressHydrationWarning
        className={`${inter.className} min-h-full flex flex-col`}
      >
        {children}
      </body>
    </html>
  );
}
