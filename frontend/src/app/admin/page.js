"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import {
  FaStore,
  FaChartBar,
  FaExclamationTriangle,
  FaCheckCircle,
  FaTimesCircle,
  FaMobileAlt,
  FaInfoCircle,
} from "react-icons/fa";
import { MdOutlineDateRange, MdTrendingDown } from "react-icons/md";
import { HiOutlineSparkles } from "react-icons/hi";
import ComboDetailModal from "../../components/admin/ComboDetailModal";
import AnalyticsDashboard from "../../components/admin/AnalyticsDashboard";

export default function AdminPage() {
  const [activeNavTab, setActiveNavTab] = useState("inventory"); // 'inventory' | 'analytics'
  const [activeTab, setActiveTab] = useState("saphethan"); // 'saphethan' | 'bancham'
  const [selectedCombo, setSelectedCombo] = useState(null);
  const [loading, setLoading] = useState(false);

  // Dummy Data state
  const [combos, setCombos] = useState([
    {
      id: 1,
      name: "Combo Phở Bò",
      discount: 25,
      confidence: 92,
      ingredients: ["Thịt Bò Bắp 500g", "Bánh Phở 300g", "Rau Thơm 100g"],
      ingredientsDetail: [
        { name: "Thịt Bò Bắp 500g", daysLeft: 2 },
        { name: "Bánh Phở 300g", daysLeft: 3 },
        { name: "Rau Thơm 100g", daysLeft: 4 },
      ],
      aiReason:
        "Nhu cầu cao cho Phở tại Quận 1. Thịt bò sắp hết hạn trong 2 ngày.",
      originalPrice: 185000,
      newPrice: 139000,
    },
    {
      id: 2,
      name: "Set Cá Hồi Nướng",
      discount: 30,
      confidence: 89,
      ingredients: ["Phi Lê Cá Hồi 400g", "Chanh 2 trái", "Măng Tây 250g"],
      ingredientsDetail: [
        { name: "Phi Lê Cá Hồi 400g", daysLeft: 3 },
        { name: "Chanh 2 trái", daysLeft: 7 },
        { name: "Măng Tây 250g", daysLeft: 4 },
      ],
      aiReason: "Xu hướng hải sản cuối tuần. Cá hồi sắp hết hạn trong 3 ngày.",
      originalPrice: 245000,
      newPrice: 172000,
    },
    {
      id: 3,
      name: "Bộ Xào Gà",
      discount: 20,
      confidence: 95,
      ingredients: ["Ức Gà 600g", "Ớt Chuông 300g", "Cà Rốt 200g"],
      ingredientsDetail: [
        { name: "Ức Gà 600g", daysLeft: 3 },
        { name: "Ớt Chuông 300g", daysLeft: 5 },
        { name: "Cà Rốt 200g", daysLeft: 6 },
      ],
      aiReason: "Món ăn phổ biến buổi tối. Gà sắp hết hạn trong 3 ngày.",
      originalPrice: 165000,
      newPrice: 132000,
    },
    {
      id: 4,
      name: "Tô Rau Cầu Vồng",
      discount: 15,
      confidence: 85,
      ingredients: ["Ớt Chuông 400g", "Cà Rốt 300g", "Quinoa 200g"],
      ingredientsDetail: [
        { name: "Ớt Chuông 400g", daysLeft: 5 },
        { name: "Cà Rốt 300g", daysLeft: 5 },
        { name: "Quinoa 200g", daysLeft: 30 },
      ],
      aiReason:
        "Người mua quan tâm sức khỏe buổi sáng. Rau sắp hết hạn trong 4-5 ngày.",
      originalPrice: 95000,
      newPrice: 81000,
    },
  ]);

  const [inventory, setInventory] = useState([
    {
      id: 1,
      name: "Thịt Bò Bắp (Cao Cấp)",
      weight: "8 kg",
      daysLeft: 2,
      limit: 7,
      status: "Khẩn Cấp",
    },
    {
      id: 2,
      name: "Phi Lê Cá Hồi Tươi",
      weight: "12 kg",
      daysLeft: 3,
      limit: 7,
      status: "Khẩn Cấp",
    },
    {
      id: 3,
      name: "Cà Rốt Organic",
      weight: "25 kg",
      daysLeft: 4,
      limit: 7,
      status: "Cảnh Báo",
    },
    {
      id: 4,
      name: "Ớt Chuông (Hỗn Hợp)",
      weight: "15 kg",
      daysLeft: 5,
      limit: 7,
      status: "Cảnh Báo",
    },
  ]);

  // TODO: FETCH DATA FROM BACKEND API
  /*
  useEffect(() => {
    const fetchDashboardData = async () => {
      setLoading(true);
      try {
        // Fetch AI Combos
        const comboRes = await fetch('/api/admin/combos'); // TODO: Replace with real endpoint
        const comboData = await comboRes.json();
        if (comboData && comboData.length > 0) setCombos(comboData);

        // Fetch Inventory Items
        const inventoryRes = await fetch('/api/admin/inventory'); // TODO: Replace with real endpoint
        const inventoryData = await inventoryRes.json();
        if (inventoryData && inventoryData.length > 0) setInventory(inventoryData);
      } catch (error) {
        console.error("Failed to load dashboard data:", error);
      } finally {
        setLoading(false);
      }
    };
    
    // Uncomment when Backend API is ready
    // fetchDashboardData();
  }, []);
  */

  const handleAcceptCombo = async (id, event) => {
    if (event) event.stopPropagation();

    // TODO: SEND ACCEPTANCE TO BACKEND API
    /*
    try {
      await fetch(`/api/admin/combos/${id}/accept`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transferToCustomer: true })
      });
    } catch (error) {
      console.error("Failed to accept combo:", error);
      alert("Có lỗi xảy ra khi gọi API");
      return; 
    }
    */

    alert("Đã chuyển Combo qua site Customer thành công!");
    setCombos((prev) => prev.filter((c) => c.id !== id));
    setSelectedCombo(null);
  };

  const handleRejectCombo = async (id, event) => {
    if (event) event.stopPropagation();

    // TODO: SEND REJECTION TO BACKEND API
    /*
    try {
      await fetch(`/api/admin/combos/${id}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
    } catch (error) {
      console.error("Failed to reject combo:", error);
      alert("Có lỗi xảy ra khi gọi API");
      return;
    }
    */

    setCombos((prev) => prev.filter((c) => c.id !== id));
  };

  return (
    <div className="min-h-screen bg-[#f8f9fc] pb-10">
      {/* Navbar */}
      <nav className="bg-white border-b border-gray-200 px-4 sm:px-6 py-3 flex flex-wrap gap-y-4 items-center justify-between sticky top-0 z-10 w-full shadow-sm">
        <div className="flex items-center space-x-2 shrink-0">
          <div className="bg-[#00b14f] p-1.5 rounded-lg text-white">
            <FaStore className="text-xl" />
          </div>
          <div>
            <h1 className="font-bold text-gray-900 text-lg leading-tight">
              FreshRoute
            </h1>
            <p className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold hidden sm:block">
              Quản Lý Giảm Lãng Phí AI
            </p>
          </div>
        </div>

        <div className="hidden lg:flex items-center space-x-8 px-8">
          <button
            onClick={() => setActiveNavTab("inventory")}
            className={`flex items-center space-x-2 font-bold pb-1 border-b-2 transition-colors ${activeNavTab === "inventory" ? "text-[#00b14f] border-[#00b14f]" : "text-gray-500 hover:text-gray-800 border-transparent"}`}
          >
            <FaStore className="text-lg" /> <span>Quản Lý Kho</span>
          </button>
          <button
            onClick={() => setActiveNavTab("analytics")}
            className={`flex items-center space-x-2 font-bold pb-1 border-b-2 transition-colors ${activeNavTab === "analytics" ? "text-[#00b14f] border-[#00b14f]" : "text-gray-500 hover:text-gray-800 border-transparent"}`}
          >
            <FaChartBar className="text-lg" /> <span>Phân Tích</span>
          </button>
        </div>

        <div className="flex items-center ml-auto sm:ml-0">
          <Link href="/customer">
            <button className="flex items-center space-x-2 bg-orange-50 hover:bg-orange-100 text-orange-600 px-4 py-2 rounded-full font-bold transition-all text-sm border border-orange-200 shadow-sm">
              <FaMobileAlt />
              <span className="hidden sm:inline">Chuyển Sang Customer App</span>
              <span className="sm:hidden">Customer App</span>
            </button>
          </Link>
        </div>
      </nav>

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6 sm:mt-8">
        {activeNavTab === "inventory" ? (
          <>
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-8 gap-4">
              <div>
                <h2 className="text-xl sm:text-2xl font-bold text-gray-900">
                  Quản Lý Kho & Combo AI
                </h2>
                <p className="text-gray-500 mt-1 text-sm font-medium">
                  Phòng chống lãng phí thông minh bằng AI
                </p>
              </div>
              <div>
                <select className="bg-white border border-gray-200 text-gray-700 text-sm rounded-lg focus:ring-[#00b14f] focus:border-[#00b14f] block w-full p-2.5 font-bold outline-none cursor-pointer shadow-sm hover:border-gray-300 transition-colors">
                  <option>Quận 1 - Trung Tâm</option>
                  <option>Quận 3 - Chi nhánh 2</option>
                  <option>Quận 7 - Cao Thắng</option>
                </select>
              </div>
            </div>
            {loading ? (
              <div className="flex justify-center items-center h-64 text-gray-500 font-semibold text-lg">
                Đang tải dữ liệu từ Backend...
              </div>
            ) : (
              <div className="flex flex-col lg:flex-row gap-6 lg:gap-8 items-start">
                {/* Left Column: AI Combos */}
                <div className="w-full lg:w-[65%]">
                  <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 sm:p-6 relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-full h-1 bg-linear-to-r from-green-400 to-[#00b14f]"></div>

                    <div className="flex justify-between items-center mb-6">
                      <div className="flex items-center space-x-2 text-[#00b14f]">
                        <HiOutlineSparkles className="text-2xl" />
                        <h3 className="text-lg font-extrabold text-gray-800 tracking-tight">
                          Combo Đề Xuất Từ AI
                        </h3>
                      </div>
                      <span className="bg-[#00b14f] text-white text-xs font-bold px-3 py-1 rounded-md shadow-sm">
                        {combos.length} Sẵn Sàng
                      </span>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 lg:gap-6">
                      {combos.map((combo) => (
                        <div
                          key={combo.id}
                          onClick={() => setSelectedCombo(combo)}
                          className="border border-gray-200 rounded-2xl p-5 hover:border-[#00b14f] hover:shadow-lg transition-all duration-300 bg-white group flex flex-col cursor-pointer"
                        >
                          <div className="flex justify-between items-start mb-2">
                            <h4 className="font-extrabold text-gray-900 text-base">
                              {combo.name}
                            </h4>
                          </div>
                          <div className="mb-4">
                            <span className="inline-block bg-orange-100 text-orange-700 text-[11px] font-extrabold px-2 py-0.5 rounded-full">
                              Giảm {combo.discount}%
                            </span>
                          </div>

                          <div className="mb-4 grow">
                            <div className="flex items-center gap-1 mb-2">
                              <span className="text-[12px] text-gray-500 font-semibold">
                                Nguyên liệu:
                              </span>
                              <FaInfoCircle className="text-blue-500 text-[10px] cursor-help" />
                            </div>
                            <div className="flex flex-wrap gap-1.5">
                              {combo.ingredients.map((ing, i) => (
                                <span
                                  key={i}
                                  className="bg-gray-100 border border-gray-200 text-gray-600 text-[11px] px-2 py-1 rounded-md font-medium"
                                >
                                  {ing}
                                </span>
                              ))}
                            </div>
                          </div>

                          <div className="bg-gray-50 p-3 rounded-xl text-[12px] text-gray-600 mb-5 border border-gray-100 leading-relaxed font-medium">
                            {combo.aiReason}
                          </div>

                          <div className="flex justify-between items-end mb-5 pb-4 border-b border-dashed border-gray-200">
                            <div>
                              <p className="text-[11px] text-gray-400 line-through mb-0.5 font-medium">
                                {combo.originalPrice.toLocaleString("vi-VN")}{" "}
                                VNĐ
                              </p>
                              <p className="text-[22px] font-black text-[#00b14f] leading-none">
                                {combo.newPrice.toLocaleString("vi-VN")}{" "}
                                <span className="text-sm font-bold">VNĐ</span>
                              </p>
                            </div>
                            <div className="text-right">
                              <p className="text-[11px] text-gray-400 mb-0.5 font-medium">
                                Tiết kiệm
                              </p>
                              <p className="text-sm font-bold text-orange-600">
                                {(
                                  combo.originalPrice - combo.newPrice
                                ).toLocaleString("vi-VN")}{" "}
                                VNĐ
                              </p>
                            </div>
                          </div>

                          <div className="flex gap-3">
                            <button
                              onClick={(e) => handleAcceptCombo(combo.id, e)}
                              className="flex-1 bg-[#00b14f] hover:bg-[#009241] text-white py-2.5 rounded-xl text-sm font-bold flex items-center justify-center gap-2 transition-colors shadow-sm"
                            >
                              <FaCheckCircle className="text-base" /> Chấp Nhận
                            </button>
                            <button
                              onClick={(e) => handleRejectCombo(combo.id, e)}
                              className="flex-1 bg-white border border-gray-300 hover:bg-gray-50 hover:text-red-500 text-gray-600 py-2.5 rounded-xl text-sm font-bold flex items-center justify-center gap-2 transition-colors shadow-sm"
                            >
                              <FaTimesCircle className="text-base" /> Từ Chối
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Right Column: Inventory List */}
                <div className="w-full lg:w-[35%] h-full">
                  <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden sticky top-24">
                    {/* Tabs */}
                    <div className="flex border-b border-gray-200 bg-gray-50/50">
                      <button
                        onClick={() => setActiveTab("saphethan")}
                        className={`flex-1 py-4 text-sm font-extrabold border-b-2 flex items-center justify-center gap-2 transition-colors ${activeTab === "saphethan" ? "border-orange-500 text-orange-600 bg-white" : "border-transparent text-gray-500 hover:text-gray-800 hover:bg-white"}`}
                      >
                        <MdOutlineDateRange className="text-xl" /> Sắp hết hạn
                      </button>
                      <button
                        onClick={() => setActiveTab("bancham")}
                        className={`flex-1 py-4 text-sm font-extrabold border-b-2 flex items-center justify-center gap-2 transition-colors ${activeTab === "bancham" ? "border-blue-500 text-blue-600 bg-white" : "border-transparent text-gray-500 hover:text-gray-800 hover:bg-white"}`}
                      >
                        <MdTrendingDown className="text-xl" /> Bán chậm
                      </button>
                    </div>

                    {/* List Items */}
                    <div className="p-4 sm:p-6">
                      <div className="flex justify-between items-center mb-6">
                        <div className="flex items-center gap-2 text-orange-500 font-extrabold">
                          <div className="bg-orange-100 p-1.5 rounded-full">
                            <FaExclamationTriangle className="text-sm" />
                          </div>
                          <span className="text-[15px] text-gray-800 tracking-tight">
                            Danh Sách Hàng Sắp Hết Hạn
                          </span>
                        </div>
                        <span className="bg-[#e91e63] text-white text-[10px] font-bold px-2 py-1 rounded shadow-sm">
                          {inventory.length} Mặt Hàng
                        </span>
                      </div>

                      <div className="space-y-4">
                        {inventory.map((item) => (
                          <div
                            key={item.id}
                            className={`p-4 rounded-xl border-l-[5px] transition-all hover:-translate-y-1 hover:shadow-md cursor-pointer bg-white ${item.status === "Khẩn Cấp" ? "border-l-[#e91e63] border-t border-r border-b border-gray-100 shadow-sm relative overflow-hidden" : "border-l-gray-800 border-t border-r border-b border-gray-100 shadow-sm"}`}
                          >
                            {item.status === "Khẩn Cấp" && (
                              <div className="absolute top-0 right-0 w-16 h-16 bg-red-50 rounded-bl-full -z-10 opacity-50"></div>
                            )}

                            <div className="flex justify-between items-start mb-3">
                              <h4 className="font-extrabold text-gray-900 text-[15px]">
                                {item.name}
                              </h4>
                              <span
                                className={`text-[10px] font-bold px-2 py-0.5 rounded-full text-white shadow-sm ${item.status === "Khẩn Cấp" ? "bg-[#e91e63]" : "bg-gray-800"}`}
                              >
                                {item.status}
                              </span>
                            </div>

                            <div className="flex items-center gap-5 text-[13px] text-gray-600 mb-4 font-semibold">
                              <span className="flex items-center gap-1.5 bg-gray-50 px-2 py-1 rounded-md border border-gray-100">
                                📦 {item.weight}
                              </span>
                              <span
                                className={`flex items-center gap-1.5 bg-gray-50 px-2 py-1 rounded-md border border-gray-100 ${item.daysLeft <= 3 ? "text-red-500" : "text-gray-600"}`}
                              >
                                📉 Còn {item.daysLeft} ngày
                              </span>
                            </div>

                            <div className="flex items-center justify-between text-[11px] text-gray-500 mb-1.5 font-medium">
                              <span>Thời gian đến hạn</span>
                              <span className="font-bold text-gray-700">
                                {item.daysLeft} / {item.limit} ngày
                              </span>
                            </div>
                            <div className="w-full bg-gray-100 rounded-full h-2 shadow-inner">
                              <div
                                className={`h-2 rounded-full transition-all duration-1000 ${item.status === "Khẩn Cấp" ? "bg-linear-to-r from-red-400 to-[#e91e63]" : "bg-linear-to-r from-gray-600 to-gray-800"}`}
                                style={{
                                  width: `${((item.limit - item.daysLeft) / item.limit) * 100}%`,
                                }}
                              ></div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        ) : (
          <AnalyticsDashboard />
        )}
      </main>

      {/* Detail Modal */}
      {selectedCombo && (
        <ComboDetailModal
          combo={selectedCombo}
          onClose={() => setSelectedCombo(null)}
          onAccept={(id) => handleAcceptCombo(id, null)}
        />
      )}
    </div>
  );
}
