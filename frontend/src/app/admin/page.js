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
import {
  acceptAdminCombo,
  fetchAdminCombos,
  fetchAdminInventory,
  rejectAdminCombo,
} from "@/lib/adminApi";

const STORE_OPTIONS = [
  { id: "BHX-HCM123", label: "BHX-HCM123 (Demo)" },
  { id: "BHX-HCM001", label: "BHX-HCM001" },
  { id: "BHX-HCM002", label: "BHX-HCM002" },
];

function toProgressWidth(item) {
  const denominator = Math.max(item.limit || 1, 1);
  const percent = ((denominator - item.daysLeft) / denominator) * 100;
  return `${Math.max(0, Math.min(100, percent))}%`;
}

export default function AdminPage() {
  const [activeNavTab, setActiveNavTab] = useState("inventory"); // 'inventory' | 'analytics'
  const [activeTab, setActiveTab] = useState("saphethan"); // 'saphethan' | 'bancham'
  const [selectedCombo, setSelectedCombo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [warning, setWarning] = useState("");
  const [storeId, setStoreId] = useState(STORE_OPTIONS[0].id);
  const [reloadToken, setReloadToken] = useState(0);
  const [combos, setCombos] = useState([]);
  const [inventory, setInventory] = useState([]);

  useEffect(() => {
    let cancelled = false;

    const fetchDashboardData = async () => {
      setLoading(true);
      setError("");
      setWarning("");

      try {
        const [comboResult, inventoryResult] = await Promise.allSettled([
          fetchAdminCombos({ storeId, limit: 10 }),
          fetchAdminInventory({ storeId, daysThreshold: 14 }),
        ]);

        const comboData =
          comboResult.status === "fulfilled" ? comboResult.value : [];
        const inventoryData =
          inventoryResult.status === "fulfilled" ? inventoryResult.value : [];

        const failures = [];
        if (comboResult.status === "rejected") {
          failures.push(
            `Combo: ${comboResult.reason?.message || "không rõ lỗi"}`,
          );
        }
        if (inventoryResult.status === "rejected") {
          failures.push(
            `Tồn kho: ${inventoryResult.reason?.message || "không rõ lỗi"}`,
          );
        }

        if (!cancelled) {
          setCombos(comboData);
          setInventory(inventoryData);
          setSelectedCombo(null);

          if (failures.length === 2) {
            setError(failures.join(" | "));
          } else if (failures.length === 1) {
            setWarning(failures[0]);
          }
        }
      } catch (fetchError) {
        if (!cancelled) {
          setCombos([]);
          setInventory([]);
          setError(fetchError.message || "Không thể tải dữ liệu admin.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    fetchDashboardData();

    return () => {
      cancelled = true;
    };
  }, [storeId, reloadToken]);

  const handleAcceptCombo = async (id, event) => {
    if (event) event.stopPropagation();

    try {
      await acceptAdminCombo({ comboId: id, storeId });
      alert("Đã chuyển Combo qua site Customer thành công!");
      setCombos((prev) => prev.filter((combo) => combo.id !== id));
      setSelectedCombo(null);
    } catch (actionError) {
      alert(actionError.message || "Có lỗi xảy ra khi gọi API");
    }
  };

  const handleRejectCombo = async (id, event) => {
    if (event) event.stopPropagation();

    try {
      await rejectAdminCombo({ comboId: id, storeId });
      setCombos((prev) => prev.filter((combo) => combo.id !== id));
      if (selectedCombo?.id === id) {
        setSelectedCombo(null);
      }
    } catch (actionError) {
      alert(actionError.message || "Có lỗi xảy ra khi gọi API");
    }
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
                <select
                  value={storeId}
                  onChange={(event) => setStoreId(event.target.value)}
                  className="bg-white border border-gray-200 text-gray-700 text-sm rounded-lg focus:ring-[#00b14f] focus:border-[#00b14f] block w-full p-2.5 font-bold outline-none cursor-pointer shadow-sm hover:border-gray-300 transition-colors"
                >
                  {STORE_OPTIONS.map((store) => (
                    <option key={store.id} value={store.id}>
                      {store.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            {loading ? (
              <div className="flex justify-center items-center h-64 text-gray-500 font-semibold text-lg">
                Đang tải dữ liệu từ Backend...
              </div>
            ) : error ? (
              <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <p className="font-semibold">{error}</p>
                <button
                  onClick={() => setReloadToken((value) => value + 1)}
                  className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg font-semibold text-sm"
                >
                  Thử lại
                </button>
              </div>
            ) : (
              <>
                {warning && (
                  <div className="w-full bg-amber-50 border border-amber-200 text-amber-800 rounded-xl p-4 mb-4 font-medium">
                    {warning}
                  </div>
                )}
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
                        {combos.length === 0 ? (
                          <div className="col-span-full text-center text-gray-500 bg-gray-50 border border-gray-200 rounded-xl py-8 px-4 font-medium">
                            Chưa có combo phù hợp cho cửa hàng đã chọn.
                          </div>
                        ) : (
                          combos.map((combo) => (
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
                              <div className="mb-4 flex flex-wrap gap-2">
                                <span className="inline-block bg-orange-100 text-orange-700 text-[11px] font-extrabold px-2 py-0.5 rounded-full">
                                  Giảm {combo.discount}%
                                </span>
                                <span className="inline-block bg-green-100 text-green-700 text-[11px] font-extrabold px-2 py-0.5 rounded-full">
                                  Tin cậy {combo.confidence}%
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
                                  {combo.ingredients.map(
                                    (ingredient, index) => (
                                      <span
                                        key={`${combo.id}-${index}`}
                                        className="bg-gray-100 border border-gray-200 text-gray-600 text-[11px] px-2 py-1 rounded-md font-medium"
                                      >
                                        {ingredient}
                                      </span>
                                    ),
                                  )}
                                </div>
                              </div>

                              <div className="bg-gray-50 p-3 rounded-xl text-[12px] text-gray-600 mb-5 border border-gray-100 leading-relaxed font-medium">
                                {combo.aiReason}
                              </div>

                              <div className="flex justify-between items-end mb-5 pb-4 border-b border-dashed border-gray-200">
                                <div>
                                  <p className="text-[11px] text-gray-400 line-through mb-0.5 font-medium">
                                    {combo.originalPrice.toLocaleString(
                                      "vi-VN",
                                    )}{" "}
                                    VNĐ
                                  </p>
                                  <p className="text-[22px] font-black text-[#00b14f] leading-none">
                                    {combo.newPrice.toLocaleString("vi-VN")}{" "}
                                    <span className="text-sm font-bold">
                                      VNĐ
                                    </span>
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
                                  onClick={(event) =>
                                    handleAcceptCombo(combo.id, event)
                                  }
                                  className="flex-1 bg-[#00b14f] hover:bg-[#009241] text-white py-2.5 rounded-xl text-sm font-bold flex items-center justify-center gap-2 transition-colors shadow-sm"
                                >
                                  <FaCheckCircle className="text-base" /> Chấp
                                  Nhận
                                </button>
                                <button
                                  onClick={(event) =>
                                    handleRejectCombo(combo.id, event)
                                  }
                                  className="flex-1 bg-white border border-gray-300 hover:bg-gray-50 hover:text-red-500 text-gray-600 py-2.5 rounded-xl text-sm font-bold flex items-center justify-center gap-2 transition-colors shadow-sm"
                                >
                                  <FaTimesCircle className="text-base" /> Từ
                                  Chối
                                </button>
                              </div>
                            </div>
                          ))
                        )}
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
                          {inventory.length === 0 ? (
                            <div className="text-center text-gray-500 bg-gray-50 border border-gray-200 rounded-xl py-8 px-4 font-medium">
                              Chưa có dữ liệu tồn kho cho cửa hàng đã chọn.
                            </div>
                          ) : (
                            inventory.map((item) => (
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
                                      width: toProgressWidth(item),
                                    }}
                                  ></div>
                                </div>
                              </div>
                            ))
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </>
            )}
          </>
        ) : (
          <AnalyticsDashboard combos={combos} inventory={inventory} />
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
