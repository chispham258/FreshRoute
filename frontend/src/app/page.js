import React from "react";
import { MdStorefront, MdOutlineQueryStats, MdAnalytics } from "react-icons/md";
import { FaMobileAlt, FaBrain } from "react-icons/fa";
import { HiOutlineSparkles } from "react-icons/hi";
import PortalCard from "../components/PortalCard";

export default function Home() {
  const adminFeatures = [
    {
      title: "Phân Tích AI & Chiến Lược",
      description:
        "Xem combo AI đang hoạt động, điểm EV và quản lý hàng sắp hết hạn",
      icon: <MdOutlineQueryStats className="text-xl text-[#00b14f]" />,
    },
    {
      title: "Bảng Phân Tích Tác Động",
      description:
        "Theo dõi giảm lãng phí, doanh thu thu hồi và tỷ lệ chuyển đổi",
      icon: <MdAnalytics className="text-xl text-[#00b14f]" />,
    },
  ];

  const customerFeatures = [
    {
      title: "Feed Combo Bữa Ăn",
      description:
        "Khám phá combo AI tạo với giá đặc biệt và giảm giá lên đến 30%",
      icon: <HiOutlineSparkles className="text-xl text-[#f37021]" />,
    },
    {
      title: "Trợ Lý AI",
      description:
        "Chat với AI để tìm món ăn, công thức và gợi ý dựa trên nguyên liệu",
      icon: <FaBrain className="text-xl text-[#f37021]" />,
    },
  ];

  return (
    <main className="min-h-screen bg-linear-to-br from-green-50 via-white to-orange-50 flex flex-col items-center justify-center p-4 lg:p-8 font-sans overflow-x-hidden">
      <header className="text-center mb-12 sm:mb-16 mt-8">
        <div className="flex items-center justify-center space-x-3 mb-5">
          <div className="bg-[#00b14f] text-white p-2 rounded-xl shadow-lg flex items-center justify-center">
            <FaBrain className="text-3xl" />
          </div>
          <h1 className="text-[40px] sm:text-[46px] font-extrabold tracking-tight text-gray-900">
            FreshRoute
          </h1>
        </div>
        <p className="text-gray-600 sm:text-lg max-w-lg mx-auto font-medium px-4">
          Nền tảng AI thông minh biến đổi hàng tồn kho sắp hết hạn thành bộ bữa
          ăn đặc biệt
        </p>
        <div className="inline-flex items-center justify-center mt-6 px-4 py-1.5 bg-green-100 text-green-700 rounded-full text-sm font-bold shadow-sm border border-green-200">
          <span className="w-2 h-2 rounded-full bg-green-500 mr-2 animate-pulse"></span>
          Powered by Gemini AI
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 lg:gap-12 w-full max-w-250 px-4 lg:px-0">
        <PortalCard
          bgColorClass="bg-[#00b14f]"
          btnColorClass="bg-[#00b14f] hover:bg-[#009241]"
          icon={<MdStorefront className="text-[42px]" />}
          title="ADMIN PORTAL"
          subtitle="Quản lý kho hàng & chiến lược AI"
          features={adminFeatures}
          buttonText="Vào Cổng Quản Trị"
          href="/admin"
        />

        <PortalCard
          bgColorClass="bg-[#f37021]"
          btnColorClass="bg-[#f37021] hover:bg-[#db621a]"
          icon={<FaMobileAlt className="text-[40px]" />}
          title="CUSTOMER APP"
          subtitle="Mua sắm bộ bữa ăn thông minh"
          features={customerFeatures}
          buttonText="Khám Phá Combo"
          href="/customer"
        />
      </div>

      <footer className="mt-16 mb-8 flex justify-center w-full px-4">
        <div className="bg-white border border-gray-200 px-6 py-3 rounded-full flex flex-wrap justify-center items-center gap-x-4 gap-y-2 text-sm font-semibold text-gray-600 shadow-sm w-fit max-w-full">
          <span className="flex items-center space-x-1 text-[#00b14f]">
            <span className="text-lg">🌱</span>
            <span>Eco-Friendly</span>
          </span>
          <span className="hidden sm:inline text-gray-300">•</span>
          <span>Tiết Kiệm Đến 30%</span>
          <span className="hidden sm:inline text-gray-300">•</span>
          <span className="text-center">Công Nghệ AI Tiên Tiến</span>
        </div>
      </footer>
    </main>
  );
}
