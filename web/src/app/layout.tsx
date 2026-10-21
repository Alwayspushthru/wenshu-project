import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "杭电校园助手 · 杭州电子科技大学",
  description: "查杭电制度，问校园办事流程。基于杭州电子科技大学公开资料，提供带来源的校园问答。",
  icons: { icon: "/hdu/crest-blue.svg" },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
