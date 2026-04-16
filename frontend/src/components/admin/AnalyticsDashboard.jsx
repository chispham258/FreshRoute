import { useState, useEffect } from "react";
import { FaMoneyBillWave, FaShoppingCart } from "react-icons/fa";

export default function AnalyticsDashboard() {
  const [timeRange, setTimeRange] = useState("Ngày");
  const [data, setData] = useState({
    totalRevenue: 48.5,
    revenueGrowth: "+18%",
    totalSold: 837,
    soldGrowth: "+23%",
    topCombos: [
      { name: "Combo Phở Bò", sold: 290 },
      { name: "Bộ Xào Gà", sold: 240 },
      { name: "Set Cá Hồi Nướng", sold: 195 },
      { name: "Tô Rau Cầu Vồng", sold: 165 },
      { name: "Pasta Ý", sold: 155 },
    ],
    revenueData: [
      { day: "T2", rev: 15000, qty: 90 },
      { day: "T3", rev: 18000, qty: 100 },
      { day: "T4", rev: 16500, qty: 95 },
      { day: "T5", rev: 21500, qty: 115 },
      { day: "T6", rev: 24500, qty: 125 },
      { day: "T7", rev: 28900, qty: 160 },
      { day: "CN", rev: 26000, qty: 145 },
    ],
  });

  // TODO: FETCH DATA FROM BACKEND API
  /*
  useEffect(() => {
    const fetchAnalytics = async () => {
      // 1. Fetch KPI Thống kê
      const kpiRes = await fetch('/api/admin/analytics/kpi?storeId=Q1');
      const kpiData = await kpiRes.json();
      
      // 2. Fetch Top Combo
      const topComboRes = await fetch('/api/admin/analytics/top-combos?storeId=Q1');
      const topComboData = await topComboRes.json();

      // 3. Fetch Doanh thu 7 ngày qua
      const seriesRes = await fetch('/api/admin/analytics/series?storeId=Q1');
      const seriesData = await seriesRes.json();

      setData({
        totalRevenue: kpiData.totalRevenue,
        ... // set data mapping API response
      });
    };
    // fetchAnalytics();
  }, []);
  */

  const maxSold = Math.max(...data.topCombos.map((c) => c.sold));

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
            <p className="text-xs text-gray-400 mt-2 font-medium">tháng này</p>
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
              Số Lượng Combo Đã Bán
            </p>
            <p className="text-4xl font-extrabold text-gray-900 leading-none">
              {data.totalSold}{" "}
              <span className="text-base text-gray-500 font-medium">combo</span>
            </p>
            <p className="text-xs text-gray-400 mt-2 font-medium">tháng này</p>
          </div>
        </div>
      </div>

      {/* Top Combo Bar Chart */}
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 max-w-full overflow-hidden">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h3 className="text-lg font-bold text-gray-900">
              Top Combo Bán Chạy
            </h3>
            <p className="text-sm text-gray-500">
              Xếp hạng combo theo số lượng bán ra
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
            <span className="w-3 h-3 bg-gray-900 rounded-sm"></span> Số Lượng
            Bán
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
            {[30000, 22500, 15000, 7500, 0].map((val, i) => (
              <div
                key={i}
                className="w-full h-0 border-t border-dashed border-gray-200 relative"
              >
                <span className="absolute -top-3 -left-13.75 text-[10px] text-gray-400 font-medium">
                  {val}
                </span>
                <span className="absolute -top-3 -right-2 sm:-right-2.5 text-[10px] text-gray-400 font-medium">
                  {val === 30000
                    ? "160"
                    : val === 22500
                      ? "120"
                      : val === 15000
                        ? "80"
                        : val === 7500
                          ? "40"
                          : "0"}
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
                const y1 = `${100 - (prev.rev / 30000) * 100}%`;
                const x2 = `${(i / (data.revenueData.length - 1)) * 100}%`;
                const y2 = `${100 - (d.rev / 30000) * 100}%`;
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
                const y1 = `${100 - (prev.qty / 160) * 100}%`;
                const x2 = `${(i / (data.revenueData.length - 1)) * 100}%`;
                const y2 = `${100 - (d.qty / 160) * 100}%`;
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
                    cy={`${100 - (d.rev / 30000) * 100}%`}
                    r="4.5"
                    fill="#00b14f"
                  />
                  <circle
                    cx={`${(i / (data.revenueData.length - 1)) * 100}%`}
                    cy={`${100 - (d.qty / 160) * 100}%`}
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
            <p className="text-lg font-bold text-[#00b14f]">21.600 VNĐ</p>
          </div>
          <div>
            <p className="text-[11px] text-gray-500 font-medium mb-1 uppercase tracking-wider">
              Cao nhất
            </p>
            <p className="text-lg font-bold text-[#2196F3]">28.900 VNĐ</p>
          </div>
          <div>
            <p className="text-[11px] text-gray-500 font-medium mb-1 uppercase tracking-wider">
              Thấp nhất
            </p>
            <p className="text-lg font-bold text-gray-700">15.200 VNĐ</p>
          </div>
          <div>
            <p className="text-[11px] text-gray-500 font-medium mb-1 uppercase tracking-wider">
              Xu hướng
            </p>
            <p className="text-lg font-bold text-[#00b14f]">↗ +18%</p>
          </div>
        </div>
      </div>
    </div>
  );
}
