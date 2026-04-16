import { useMemo, useState } from "react";
import { FaMoneyBillWave, FaShoppingCart } from "react-icons/fa";

const DAY_LABELS = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"];

export default function AnalyticsDashboard({ combos = [], inventory = [] }) {
  const [timeRange, setTimeRange] = useState("Ngày");

  const data = useMemo(() => {
    const safeCombos = Array.isArray(combos) ? combos : [];
    const safeInventory = Array.isArray(inventory) ? inventory : [];

    const totalRevenueValue = safeCombos.reduce(
      (sum, combo) => sum + Number(combo.newPrice || 0),
      0,
    );

    const criticalCount = safeInventory.filter(
      (item) => item.status === "Khẩn Cấp",
    ).length;
    const warningCount = safeInventory.filter(
      (item) => item.status === "Cảnh Báo",
    ).length;

    const topCombos = safeCombos
      .slice()
      .sort((a, b) => Number(b.confidence || 0) - Number(a.confidence || 0))
      .slice(0, 5)
      .map((item) => ({
        name: item.name,
        sold: Math.round(Number(item.confidence || 0)),
      }));

    const revenuePerDay = Math.round(totalRevenueValue / DAY_LABELS.length);
    const revenueData = DAY_LABELS.map((day) => ({
      day,
      rev: revenuePerDay,
      qty: safeCombos.length,
    }));

    return {
      totalRevenue: Number((totalRevenueValue / 1_000_000).toFixed(2)),
      revenueGrowth:
        criticalCount > 0 ? `${criticalCount} khẩn cấp` : "Ổn định",
      totalSold: safeCombos.length,
      soldGrowth: warningCount > 0 ? `${warningCount} cảnh báo` : "Ổn định",
      topCombos:
        topCombos.length > 0
          ? topCombos
          : [{ name: "Chưa có dữ liệu", sold: 0 }],
      revenueData,
    };
  }, [combos, inventory]);

  const maxSold = Math.max(1, ...data.topCombos.map((combo) => combo.sold));
  const maxRevenue = Math.max(1, ...data.revenueData.map((item) => item.rev));
  const maxQty = Math.max(1, ...data.revenueData.map((item) => item.qty));
  const revenueTicks = [1, 0.75, 0.5, 0.25, 0].map((ratio) =>
    Math.round(maxRevenue * ratio),
  );
  const quantityTicks = [1, 0.75, 0.5, 0.25, 0].map((ratio) =>
    Math.round(maxQty * ratio),
  );

  const averageRevenue =
    data.revenueData.reduce((sum, item) => sum + item.rev, 0) /
    data.revenueData.length;
  const highestRevenue = Math.max(...data.revenueData.map((item) => item.rev));
  const lowestRevenue = Math.min(...data.revenueData.map((item) => item.rev));
  const firstDayRevenue = data.revenueData[0]?.rev || 0;
  const lastDayRevenue =
    data.revenueData[data.revenueData.length - 1]?.rev || 0;
  const trendPercent =
    firstDayRevenue > 0
      ? ((lastDayRevenue - firstDayRevenue) / firstDayRevenue) * 100
      : 0;

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* 2 KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full">
        <div className="bg-white rounded-2xl p-6 border border-gray-200 shadow-sm flex flex-col justify-between h-40">
          <div className="flex justify-between items-start">
            <div className="bg-[#00b14f] text-white p-3 rounded-xl shadow-md shadow-green-200/50">
              <FaMoneyBillWave className="text-xl" />
            </div>
            <span className="bg-green-100 text-[#00b14f] text-xs font-bold px-2.5 py-1 rounded-full">
              {data.revenueGrowth}
            </span>
          </div>
          <div>
            <p className="text-gray-500 font-medium text-sm mb-1">
              Tổng Doanh Thu
            </p>
            <p className="text-4xl font-extrabold text-gray-900 leading-none">
              {data.totalRevenue}{" "}
              <span className="text-base text-gray-500 font-medium">
                Triệu VNĐ
              </span>
            </p>
            <p className="text-xs text-gray-400 mt-2 font-medium">
              theo dữ liệu hiện tại
            </p>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-6 border border-gray-200 shadow-sm flex flex-col justify-between h-40">
          <div className="flex justify-between items-start">
            <div className="bg-orange-500 text-white p-3 rounded-xl shadow-md shadow-orange-200/50">
              <FaShoppingCart className="text-xl" />
            </div>
            <span className="bg-orange-100 text-orange-600 text-xs font-bold px-2.5 py-1 rounded-full">
              {data.soldGrowth}
            </span>
          </div>
          <div>
            <p className="text-gray-500 font-medium text-sm mb-1">
              Số Combo Đề Xuất
            </p>
            <p className="text-4xl font-extrabold text-gray-900 leading-none">
              {data.totalSold}{" "}
              <span className="text-base text-gray-500 font-medium">combo</span>
            </p>
            <p className="text-xs text-gray-400 mt-2 font-medium">
              theo dữ liệu hiện tại
            </p>
          </div>
        </div>
      </div>

      {/* Top Combo Bar Chart */}
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 max-w-full overflow-hidden">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h3 className="text-lg font-bold text-gray-900">
              Top Combo Theo Độ Tin Cậy AI
            </h3>
            <p className="text-sm text-gray-500">
              Xếp hạng combo theo điểm confidence từ backend
            </p>
          </div>
          <span className="bg-blue-50 text-blue-600 border border-blue-100 text-xs font-bold px-2 py-1 flex items-center gap-1.5 rounded pr-2.5 shadow-sm">
            <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse ml-0.5"></span>{" "}
            Top 5
          </span>
        </div>

        <div className="space-y-5 pb-6 pt-2 border-l-2 border-gray-100 pl-4 sm:pl-6 ml-16 sm:ml-30 relative">
          {data.topCombos.map((item, idx) => {
            const pct = (item.sold / maxSold) * 100;
            const isTop1 = idx === 0;
            return (
              <div key={idx} className="relative flex items-center group">
                {/* Label Outside */}
                <div className="absolute -left-22.5 sm:-left-35 w-20 sm:w-32 text-right pr-2 text-xs sm:text-sm font-medium text-gray-600 truncate">
                  {item.name}
                </div>

                {/* CSS Bar */}
                <div className="w-full h-8 sm:h-10 bg-gray-50/50 rounded-r-lg relative overflow-hidden border border-gray-100 group-hover:border-gray-200 transition-colors">
                  <div
                    className={`h-full flex items-center px-4 rounded-r-lg transition-all duration-1000 origin-left ease-out ${isTop1 ? "bg-[#ff9800]" : "bg-[#00c853]"}`}
                    style={{ width: `${pct}%` }}
                  ></div>
                </div>
                <div className="ml-3 text-xs sm:text-sm font-bold text-gray-700 w-8">
                  {item.sold}
                </div>
              </div>
            );
          })}

          {/* Grid lines (visual only) */}
          <div className="absolute top-0 bottom-0 left-0 border-l border-gray-200/50 border-dashed"></div>
          <div className="absolute top-0 bottom-0 left-1/4 border-l border-gray-200/50 border-dashed"></div>
          <div className="absolute top-0 bottom-0 left-2/4 border-l border-gray-200/50 border-dashed"></div>
          <div className="absolute top-0 bottom-0 left-3/4 border-l border-gray-200/50 border-dashed"></div>
          <div className="absolute top-0 bottom-0 right-0 border-l border-gray-200/50 border-dashed hidden sm:block"></div>
        </div>

        {/* Legend */}
        <div className="flex justify-center items-center mt-2 border-t border-gray-100 pt-4">
          <div className="flex items-center gap-1.5 text-sm font-medium text-gray-800">
            <span className="w-3 h-3 bg-gray-900 rounded-sm"></span> Điểm Tin
            Cậy
          </div>
        </div>
      </div>

      {/* Revenue Over Time Chart */}
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 overflow-hidden">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-8 gap-4">
          <div>
            <h3 className="text-lg font-bold text-gray-900">
              Doanh Thu Theo Thời Gian
            </h3>
            <p className="text-sm text-gray-500">
              Biểu đồ xu hướng doanh thu từ combo
            </p>
          </div>
          <div className="bg-gray-50 p-1 flex rounded-lg">
            <button
              onClick={() => setTimeRange("Ngày")}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors ${timeRange === "Ngày" ? "bg-white shadow-sm font-bold text-gray-800 border border-gray-200/60" : "font-semibold text-gray-500 hover:text-gray-800 border border-transparent"}`}
            >
              Ngày
            </button>
            <button
              onClick={() => setTimeRange("Tuần")}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors ${timeRange === "Tuần" ? "bg-white shadow-sm font-bold text-gray-800 border border-gray-200/60" : "font-semibold text-gray-500 hover:text-gray-800 border border-transparent"}`}
            >
              Tuần
            </button>
            <button
              onClick={() => setTimeRange("Tháng")}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors ${timeRange === "Tháng" ? "bg-white shadow-sm font-bold text-gray-800 border border-gray-200/60" : "font-semibold text-gray-500 hover:text-gray-800 border border-transparent"}`}
            >
              Tháng
            </button>
          </div>
        </div>

        {/* Since recharts is not available, we use SVG to render the chart closely matching the design */}
        <div className="w-full relative h-75 sm:h-87.5 font-sans">
          {/* Y Axis Grid */}
          <div className="absolute inset-0 flex flex-col justify-between z-0 pb-6 pr-5 sm:pr-10 pl-13.75">
            {revenueTicks.map((value, index) => (
              <div
                key={index}
                className="w-full h-0 border-t border-dashed border-gray-200 relative"
              >
                <span className="absolute -top-3 -left-13.75 text-[10px] text-gray-400 font-medium">
                  {value}
                </span>
                <span className="absolute -top-3 -right-2 sm:-right-2.5 text-[10px] text-gray-400 font-medium">
                  {quantityTicks[index]}
                </span>
              </div>
            ))}
          </div>

          <div className="absolute left-2 sm:left-2 top-14 -rotate-90 text-[10px] text-gray-400 font-medium origin-center hidden sm:block">
            Doanh thu (VNĐ)
          </div>
          <div className="absolute right-0 top-14 rotate-90 text-[10px] text-gray-400 font-medium origin-center hidden sm:block">
            Số combo
          </div>

          {/* SVG Line Graph */}
          <div className="absolute inset-0 pb-6 pr-5 sm:pr-10 pl-13.75 z-10 w-full h-75 sm:h-87.5">
            <svg width="100%" height="100%" className="overflow-visible">
              <defs>
                {/* Create a smoother path using cubic bezier approximations -> Simplified to straight lines & smoothing based on width% */}
              </defs>

              {/* Green Line (Doanh Thu) mapped 0 -> 30000 */}
              {data.revenueData.map((d, i) => {
                if (i === 0) return null;
                const prev = data.revenueData[i - 1];
                const x1 = `${((i - 1) / (data.revenueData.length - 1)) * 100}%`;
                const y1 = `${100 - (prev.rev / maxRevenue) * 100}%`;
                const x2 = `${(i / (data.revenueData.length - 1)) * 100}%`;
                const y2 = `${100 - (d.rev / maxRevenue) * 100}%`;
                return (
                  <line
                    key={`rev-${i}`}
                    x1={x1}
                    y1={y1}
                    x2={x2}
                    y2={y2}
                    stroke="#00b14f"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                  />
                );
              })}

              {/* Orange Line (Số lượng) mapped 0 -> 160 */}
              {data.revenueData.map((d, i) => {
                if (i === 0) return null;
                const prev = data.revenueData[i - 1];
                const x1 = `${((i - 1) / (data.revenueData.length - 1)) * 100}%`;
                const y1 = `${100 - (prev.qty / maxQty) * 100}%`;
                const x2 = `${(i / (data.revenueData.length - 1)) * 100}%`;
                const y2 = `${100 - (d.qty / maxQty) * 100}%`;
                return (
                  <line
                    key={`qty-${i}`}
                    x1={x1}
                    y1={y1}
                    x2={x2}
                    y2={y2}
                    stroke="#ff9800"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                  />
                );
              })}

              {/* Points */}
              {data.revenueData.map((d, i) => (
                <g key={`pt-${i}`}>
                  <circle
                    cx={`${(i / (data.revenueData.length - 1)) * 100}%`}
                    cy={`${100 - (d.rev / maxRevenue) * 100}%`}
                    r="4.5"
                    fill="#00b14f"
                  />
                  <circle
                    cx={`${(i / (data.revenueData.length - 1)) * 100}%`}
                    cy={`${100 - (d.qty / maxQty) * 100}%`}
                    r="4.5"
                    fill="#ff9800"
                  />
                </g>
              ))}
            </svg>

            {/* X Axis Labels */}
            <div className="absolute -bottom-1 left-13.75 right-5 sm:right-10 flex justify-between z-10">
              {data.revenueData.map((d, idx) => (
                <div
                  key={idx}
                  className="text-[11px] font-medium text-gray-500 w-4 text-center -ml-2 -translate-y-2"
                >
                  {d.day}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Legend */}
        <div className="flex justify-center gap-6 items-center mt-6">
          <div className="flex items-center gap-1.5 text-sm font-semibold text-[#00b14f]">
            <span className="flex items-center">
              <span className="w-1.5 h-1.5 rounded-full bg-[#00b14f] -mr-0.5"></span>
              <span className="w-4 h-0.5 bg-[#00b14f]"></span>
              <span className="w-1.5 h-1.5 rounded-full bg-[#00b14f] -ml-0.5"></span>
            </span>{" "}
            Doanh Thu
          </div>
          <div className="flex items-center gap-1.5 text-sm font-semibold text-[#ff9800]">
            <span className="flex items-center">
              <span className="w-1.5 h-1.5 rounded-full bg-[#ff9800] -mr-0.5"></span>
              <span className="w-4 h-0.5 bg-[#ff9800]"></span>
              <span className="w-1.5 h-1.5 rounded-full bg-[#ff9800] -ml-0.5"></span>
            </span>{" "}
            Số Combo
          </div>
        </div>

        {/* Footer Stats block */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-8 pt-6 border-t border-gray-100 text-center">
          <div>
            <p className="text-[11px] text-gray-500 font-medium mb-1 uppercase tracking-wider">
              Trung bình / ngày
            </p>
            <p className="text-lg font-bold text-[#00b14f]">
              {Math.round(averageRevenue).toLocaleString("vi-VN")} VNĐ
            </p>
          </div>
          <div>
            <p className="text-[11px] text-gray-500 font-medium mb-1 uppercase tracking-wider">
              Cao nhất
            </p>
            <p className="text-lg font-bold text-[#2196F3]">
              {highestRevenue.toLocaleString("vi-VN")} VNĐ
            </p>
          </div>
          <div>
            <p className="text-[11px] text-gray-500 font-medium mb-1 uppercase tracking-wider">
              Thấp nhất
            </p>
            <p className="text-lg font-bold text-gray-700">
              {lowestRevenue.toLocaleString("vi-VN")} VNĐ
            </p>
          </div>
          <div>
            <p className="text-[11px] text-gray-500 font-medium mb-1 uppercase tracking-wider">
              Xu hướng
            </p>
            <p
              className={`text-lg font-bold ${trendPercent >= 0 ? "text-[#00b14f]" : "text-red-500"}`}
            >
              {trendPercent >= 0 ? "↗" : "↘"} {trendPercent >= 0 ? "+" : ""}
              {trendPercent.toFixed(1)}%
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
