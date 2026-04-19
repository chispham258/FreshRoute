"use client";
import { useState, useEffect, useMemo } from "react";
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
import { HiOutlineSparkles } from "react-icons/hi";
import ComboDetailModal from "../../components/admin/ComboDetailModal";
import AnalyticsDashboard from "../../components/admin/AnalyticsDashboard";
import {
  acceptAdminCombo,
  fetchAdminCombos,
  fetchAdminInventory,
  rejectAdminCombo,
} from "@/lib/adminApi";
import { formatVnd } from "@/lib/currency";

const STORE_OPTIONS = [{ id: "BHX-HCM001", label: "BHX-HCM001" }];
const ADMIN_COMBO_CACHE_KEY = "freshroute_admin_combo_cache_v1";
const INVENTORY_PAGE_SIZE = 6;

function getLocalDateKey(date = new Date()) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function readAdminComboCache(storeId) {
  if (typeof window === "undefined") return null;

  try {
    const raw = localStorage.getItem(ADMIN_COMBO_CACHE_KEY);
    if (!raw) return null;

    const parsed = JSON.parse(raw);
    const entry = parsed?.[storeId];

    if (!entry) return null;
    if (entry.dateKey !== getLocalDateKey()) return null;
    if (!Array.isArray(entry.combos)) return null;

    return {
      combos: entry.combos,
      analyzedAt: entry.analyzedAt || null,
    };
  } catch {
    return null;
  }
}

function writeAdminComboCache(storeId, combos, analyzedAt) {
  if (typeof window === "undefined") return analyzedAt;

  const safeAnalyzedAt = analyzedAt || new Date().toISOString();

  try {
    const raw = localStorage.getItem(ADMIN_COMBO_CACHE_KEY);
    const parsed = raw ? JSON.parse(raw) : {};

    parsed[storeId] = {
      dateKey: getLocalDateKey(),
      analyzedAt: safeAnalyzedAt,
      combos: Array.isArray(combos) ? combos : [],
    };

    localStorage.setItem(ADMIN_COMBO_CACHE_KEY, JSON.stringify(parsed));
  } catch {
    // Ignore cache write failures and keep UI functional.
  }

  return safeAnalyzedAt;
}

function formatAnalyzedAt(value) {
  if (!value) return "Chưa có dữ liệu";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Chưa có dữ liệu";

  return date.toLocaleString("vi-VN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

function toProgressWidth(item) {
  const denominator = Math.max(item.limit || 1, 1);
  const percent = ((denominator - item.daysLeft) / denominator) * 100;
  return `${Math.max(0, Math.min(100, percent))}%`;
}

function getInventoryStatusClasses(status) {
  if (status === "Khẩn Cấp") {
    return "bg-red-100 text-red-700";
  }

  if (status === "Cảnh Báo") {
    return "bg-amber-100 text-amber-700";
  }

  return "bg-gray-100 text-gray-700";
}

export default function AdminPage() {
  const [activeNavTab, setActiveNavTab] = useState("inventory"); // 'inventory' | 'analytics'
  const [selectedCombo, setSelectedCombo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [warning, setWarning] = useState("");
  const [storeId, setStoreId] = useState(STORE_OPTIONS[0].id);
  const [reloadToken, setReloadToken] = useState(0);
  const [combos, setCombos] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [comboAnalyzedAt, setComboAnalyzedAt] = useState(null);
  const [comboDataSource, setComboDataSource] = useState("");
  const [recallingCombos, setRecallingCombos] = useState(false);
  const [combosApiLoading, setCombosApiLoading] = useState(false);
  const [inventoryStatusFilter, setInventoryStatusFilter] = useState("all");
  const [inventorySortMode, setInventorySortMode] = useState("expiry");
  const [inventoryPage, setInventoryPage] = useState(1);

  const inventoryStatusOptions = useMemo(() => {
    const statuses = Array.from(
      new Set(
        inventory
          .map((item) => item.status)
          .filter((status) => typeof status === "string" && status.length > 0),
      ),
    );

    return statuses;
  }, [inventory]);

  const filteredInventory = useMemo(() => {
    const baseInventory =
      inventoryStatusFilter === "all"
        ? inventory
        : inventory.filter((item) => item.status === inventoryStatusFilter);

    const sortedInventory = [...baseInventory].sort((left, right) => {
      if (inventorySortMode === "name") {
        return left.name.localeCompare(right.name, "vi");
      }

      return left.daysLeft - right.daysLeft;
    });

    return sortedInventory;
  }, [inventory, inventoryStatusFilter, inventorySortMode]);

  const inventoryTotalPages = Math.max(
    1,
    Math.ceil(filteredInventory.length / INVENTORY_PAGE_SIZE),
  );

  const currentInventoryPage = Math.min(inventoryPage, inventoryTotalPages);

  const paginatedInventory = useMemo(() => {
    const startIndex = (currentInventoryPage - 1) * INVENTORY_PAGE_SIZE;
    return filteredInventory.slice(
      startIndex,
      startIndex + INVENTORY_PAGE_SIZE,
    );
  }, [filteredInventory, currentInventoryPage]);

  const inventoryRangeStart =
    filteredInventory.length === 0
      ? 0
      : (currentInventoryPage - 1) * INVENTORY_PAGE_SIZE + 1;
  const inventoryRangeEnd = Math.min(
    currentInventoryPage * INVENTORY_PAGE_SIZE,
    filteredInventory.length,
  );

  useEffect(() => {
    setInventoryPage(1);
  }, [storeId, inventoryStatusFilter, inventorySortMode]);

  useEffect(() => {
    if (inventoryPage > inventoryTotalPages) {
      setInventoryPage(inventoryTotalPages);
    }
  }, [inventoryPage, inventoryTotalPages]);

  useEffect(() => {
    let cancelled = false;

    const fetchDashboardData = async () => {
      setLoading(true);
      setError("");
      setWarning("");

      try {
        const cachedComboEntry = readAdminComboCache(storeId);

        const [comboResult, inventoryResult] = await Promise.allSettled([
          cachedComboEntry
            ? Promise.resolve({
                combos: cachedComboEntry.combos,
                analyzedAt: cachedComboEntry.analyzedAt,
                source: "cache",
              })
            : (async () => {
                if (!cancelled) {
                  setCombosApiLoading(true);
                }

                try {
                  const comboData = await fetchAdminCombos({
                    storeId,
                    limit: 10,
                  });
                  const analyzedAt = writeAdminComboCache(
                    storeId,
                    comboData,
                    new Date().toISOString(),
                  );

                  return {
                    combos: comboData,
                    analyzedAt,
                    source: "api",
                  };
                } finally {
                  if (!cancelled) {
                    setCombosApiLoading(false);
                  }
                }
              })(),
          fetchAdminInventory({ storeId, daysThreshold: 14 }),
        ]);

        const comboData =
          comboResult.status === "fulfilled" ? comboResult.value.combos : [];
        const analyzedAt =
          comboResult.status === "fulfilled"
            ? comboResult.value.analyzedAt || null
            : null;
        const comboSource =
          comboResult.status === "fulfilled" ? comboResult.value.source : "";
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
          setComboAnalyzedAt(analyzedAt);
          setComboDataSource(comboSource);
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

    const combo = combos.find((c) => c.id === id);
    if (!combo) return;

    try {
      await acceptAdminCombo({ comboId: id, storeId, combo });
      alert("Đã chuyển Combo qua site Customer thành công!");
      setCombos((prev) => {
        const next = prev.filter((c) => c.id !== id);
        writeAdminComboCache(storeId, next, comboAnalyzedAt);
        return next;
      });
      setSelectedCombo(null);
    } catch (actionError) {
      alert(actionError.message || "Có lỗi xảy ra khi gọi API");
    }
  };

  const handleRejectCombo = async (id, event) => {
    if (event) event.stopPropagation();

    try {
      await rejectAdminCombo({ comboId: id, storeId });
      setCombos((prev) => {
        const next = prev.filter((combo) => combo.id !== id);
        writeAdminComboCache(storeId, next, comboAnalyzedAt);
        return next;
      });
      if (selectedCombo?.id === id) {
        setSelectedCombo(null);
      }
    } catch (actionError) {
      alert(actionError.message || "Có lỗi xảy ra khi gọi API");
    }
  };

  const handleRecallCombos = async () => {
    setRecallingCombos(true);
    setCombosApiLoading(true);
    setWarning("");

    try {
      const comboData = await fetchAdminCombos({ storeId, limit: 10 });
      const analyzedAt = writeAdminComboCache(
        storeId,
        comboData,
        new Date().toISOString(),
      );

      setCombos(comboData);
      setComboAnalyzedAt(analyzedAt);
      setComboDataSource("api");
      setSelectedCombo(null);
    } catch (recallError) {
      setWarning(`Combo: ${recallError.message || "không rõ lỗi"}`);
    } finally {
      setRecallingCombos(false);
      setCombosApiLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f8f9fc] pb-10">
      {combosApiLoading && (
        <div className="fixed inset-0 z-100 bg-black/35 backdrop-blur-[1px] flex items-center justify-center px-4">
          <div className="bg-white rounded-2xl shadow-2xl border border-gray-200 px-6 py-5 w-full max-w-sm text-center">
            <div className="mx-auto mb-3 h-9 w-9 rounded-full border-4 border-gray-200 border-t-[#00b14f] animate-spin" />
            <p className="text-gray-900 font-extrabold text-base">
              AI đang phân tích combo
            </p>
            <p className="text-gray-500 text-sm mt-1 font-medium">
              Vui lòng chờ trong giây lát...
            </p>
          </div>
        </div>
      )}

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

                      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-4 mb-6">
                        <div>
                          <div className="flex items-center space-x-2 text-[#00b14f]">
                            <HiOutlineSparkles className="text-2xl" />
                            <h3 className="text-lg font-extrabold text-gray-800 tracking-tight">
                              Combo Đề Xuất Từ AI
                            </h3>
                          </div>
                          <p className="text-[12px] text-gray-500 mt-1 font-medium">
                            Lần phân tích gần nhất:{" "}
                            {formatAnalyzedAt(comboAnalyzedAt)}
                            {comboDataSource === "cache"
                              ? " (từ bộ nhớ trình duyệt)"
                              : ""}
                          </p>
                        </div>

                        <div className="flex items-center gap-2">
                          <button
                            onClick={handleRecallCombos}
                            disabled={recallingCombos}
                            className="bg-white border border-[#00b14f] text-[#00b14f] hover:bg-green-50 disabled:opacity-60 disabled:cursor-not-allowed px-3 py-1.5 rounded-md text-xs font-bold transition-colors"
                          >
                            {recallingCombos
                              ? "Đang phân tích..."
                              : "Phân tích lại"}
                          </button>
                          <span className="bg-[#00b14f] text-white text-xs font-bold px-3 py-1 rounded-md shadow-sm whitespace-nowrap">
                            {combos.length} Sẵn Sàng
                          </span>
                        </div>
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
                                    {formatVnd(combo.originalPrice)}
                                  </p>
                                  <p className="text-[22px] font-black text-[#00b14f] leading-none">
                                    {formatVnd(combo.newPrice)}
                                  </p>
                                </div>
                                <div className="text-right">
                                  <p className="text-[11px] text-gray-400 mb-0.5 font-medium">
                                    Tiết kiệm
                                  </p>
                                  <p className="text-sm font-bold text-orange-600">
                                    {formatVnd(
                                      combo.originalPrice - combo.newPrice,
                                    )}
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
                      {/* List Items */}
                      <div className="p-4 sm:p-6">
                        <div className="flex justify-between items-center mb-4">
                          <div className="flex items-center gap-2 text-orange-500 font-extrabold">
                            <div className="bg-orange-100 p-1.5 rounded-full">
                              <FaExclamationTriangle className="text-sm" />
                            </div>
                            <span className="text-[15px] text-gray-800 tracking-tight">
                              Danh Sách Hàng Sắp Hết Hạn
                            </span>
                          </div>
                          <span className="bg-[#e91e63] text-white text-[10px] font-bold px-2 py-1 rounded shadow-sm">
                            {filteredInventory.length} / {inventory.length} Mặt
                            Hàng
                          </span>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-4">
                          <div className="flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-lg px-2 py-2">
                            <span className="text-[11px] font-semibold text-gray-500 shrink-0">
                              Lọc:
                            </span>
                            <select
                              value={inventoryStatusFilter}
                              onChange={(event) => {
                                setInventoryStatusFilter(event.target.value);
                                setInventoryPage(1);
                              }}
                              className="w-full bg-white border border-gray-200 text-gray-700 text-[12px] font-semibold rounded-md px-2 py-1.5 outline-none"
                            >
                              <option value="all">Tất cả trạng thái</option>
                              {inventoryStatusOptions.map((status) => (
                                <option key={status} value={status}>
                                  {status}
                                </option>
                              ))}
                            </select>
                          </div>

                          <div className="flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-lg p-1">
                            <button
                              onClick={() => setInventorySortMode("expiry")}
                              className={`flex-1 text-[12px] font-bold rounded-md px-2 py-1.5 transition-colors ${inventorySortMode === "expiry" ? "bg-white text-orange-600 border border-orange-200" : "text-gray-500 hover:text-gray-800"}`}
                            >
                              Gần hết hạn
                            </button>
                            <button
                              onClick={() => setInventorySortMode("name")}
                              className={`flex-1 text-[12px] font-bold rounded-md px-2 py-1.5 transition-colors ${inventorySortMode === "name" ? "bg-white text-blue-600 border border-blue-200" : "text-gray-500 hover:text-gray-800"}`}
                            >
                              Tên A-Z
                            </button>
                          </div>
                        </div>

                        <div className="space-y-3">
                          {filteredInventory.length === 0 ? (
                            <div className="text-center text-gray-500 bg-gray-50 border border-gray-200 rounded-xl py-8 px-4 font-medium">
                              Không có dữ liệu phù hợp với bộ lọc hiện tại.
                            </div>
                          ) : (
                            paginatedInventory.map((item) => (
                              <div
                                key={item.id}
                                className="p-3 rounded-xl border border-gray-200 bg-white"
                              >
                                <div className="flex justify-between items-start gap-3 mb-2">
                                  <h4 className="font-bold text-gray-900 text-[14px] leading-tight">
                                    {item.name}
                                  </h4>
                                  <span
                                    className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${getInventoryStatusClasses(item.status)}`}
                                  >
                                    {item.status}
                                  </span>
                                </div>

                                <div className="grid grid-cols-2 gap-2 text-[12px] text-gray-600 font-medium mb-2">
                                  <p>
                                    Khối lượng:{" "}
                                    <span className="font-bold">
                                      {item.weight}
                                    </span>
                                  </p>
                                  <p>
                                    Còn lại:{" "}
                                    <span
                                      className={`font-bold ${item.daysLeft <= 3 ? "text-red-600" : "text-gray-800"}`}
                                    >
                                      {item.daysLeft} ngày
                                    </span>
                                  </p>
                                </div>

                                <div className="flex items-center justify-between text-[11px] text-gray-500 mb-1 font-medium">
                                  <span>Thời gian đến hạn</span>
                                  <span className="font-bold text-gray-700">
                                    {item.daysLeft} / {item.limit} ngày
                                  </span>
                                </div>
                                <div className="w-full bg-gray-100 rounded-full h-1.5">
                                  <div
                                    className={`h-1.5 rounded-full transition-all duration-700 ${item.status === "Khẩn Cấp" ? "bg-red-500" : item.status === "Cảnh Báo" ? "bg-amber-500" : "bg-gray-500"}`}
                                    style={{
                                      width: toProgressWidth(item),
                                    }}
                                  ></div>
                                </div>
                              </div>
                            ))
                          )}
                        </div>

                        {filteredInventory.length > 0 && (
                          <div className="mt-4 pt-4 border-t border-gray-100 flex items-center justify-between gap-2">
                            <p className="text-[11px] text-gray-500 font-medium">
                              Hiển thị {inventoryRangeStart}-{inventoryRangeEnd}{" "}
                              / {filteredInventory.length}
                            </p>
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() =>
                                  setInventoryPage((prev) =>
                                    Math.max(1, prev - 1),
                                  )
                                }
                                disabled={currentInventoryPage === 1}
                                className="px-2.5 py-1 text-[12px] font-bold border border-gray-200 rounded-md text-gray-700 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-50"
                              >
                                Trước
                              </button>
                              <span className="text-[11px] text-gray-600 font-semibold min-w-17 text-center">
                                Trang {currentInventoryPage}/
                                {inventoryTotalPages}
                              </span>
                              <button
                                onClick={() =>
                                  setInventoryPage((prev) =>
                                    Math.min(inventoryTotalPages, prev + 1),
                                  )
                                }
                                disabled={
                                  currentInventoryPage === inventoryTotalPages
                                }
                                className="px-2.5 py-1 text-[12px] font-bold border border-gray-200 rounded-md text-gray-700 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-50"
                              >
                                Sau
                              </button>
                            </div>
                          </div>
                        )}
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
