import { FaBoxOpen, FaChartLine } from "react-icons/fa";
import { SiProbot } from "react-icons/si";

export default function ComboDetailModal({ combo, onClose, onAccept }) {
  if (!combo) return null;

  const ingredientsDetail = Array.isArray(combo.ingredientsDetail)
    ? combo.ingredientsDetail
    : [];
  const originalPrice = Number(combo.originalPrice || 0);
  const newPrice = Number(combo.newPrice || 0);
  const discountValue = Math.max(originalPrice - newPrice, 0);

  return (
    <div
      className="fixed inset-0 z-50 flex justify-center bg-black/10 backdrop-blur-sm p-4 overflow-y-auto animate-in fade-in duration-200"
      onClick={onClose}
    >
      {/* Container simulating the exact design */}
      <div
        className="bg-[#f8f9fc] w-full max-w-160 rounded-2xl shadow-2xl relative my-auto flex flex-col h-auto overflow-hidden border border-gray-200"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="overflow-y-auto w-full p-4 sm:p-5 space-y-4 scroll-smooth">
          {/* Card 1: Title & Tags */}
          <div className="bg-white rounded-xl p-5 shadow-xs border border-gray-100 flex flex-col">
            <h2 className="text-[17px] font-bold text-gray-800 leading-tight mb-4">
              {combo.name || "Combo chưa đặt tên"}
            </h2>
            <div className="flex flex-wrap gap-2">
              <span className="px-2.5 py-1 bg-orange-50 border border-orange-200 text-orange-400 text-[11px] font-semibold rounded-[20px]">
                Giảm {combo.discount || 0}%
              </span>
              <span className="px-2.5 py-1 bg-green-50 border border-green-200 text-[#00b14f] text-[11px] font-semibold rounded-[20px]">
                Tin cậy {combo.confidence || 0}%
              </span>
            </div>
          </div>

          {/* Card 3: Products */}
          <div className="bg-white rounded-xl p-5 shadow-xs border border-gray-100">
            <h3 className="text-[15px] font-bold text-gray-800 mb-5 tracking-tight border-b border-gray-100 pb-3">
              Sản phẩm trong combo
            </h3>

            <div className="space-y-4">
              {ingredientsDetail.length > 0 ? (
                ingredientsDetail.map((ing, i) => (
                  <div
                    key={i}
                    className={`flex justify-between items-start ${i !== ingredientsDetail.length - 1 ? "pb-4 border-b border-gray-100" : ""}`}
                  >
                    <div className="flex-1 pr-4">
                      <div className="font-bold text-gray-800 text-[14px] mb-0.5">
                        {ing.name || "Nguyên liệu"}
                      </div>
                      <div className="text-[12px] text-gray-400 mb-2">
                        {ing.weight || "Không có dữ liệu định lượng"}
                      </div>
                      <span className="inline-block px-2.5 py-0.5 bg-orange-50 border border-orange-200 text-orange-400 text-[11px] font-semibold rounded-[20px] whitespace-nowrap">
                        Trạng thái: {ing.status || "Bình Thường"}
                      </span>
                    </div>
                    <div className="font-bold text-gray-800 text-[14px] shrink-0 text-right whitespace-nowrap">
                      <span className="font-semibold text-[13px] underline underline-offset-[3px] mr-px">
                        đ
                      </span>
                      {typeof ing.price === "number"
                        ? ing.price.toLocaleString("vi-VN")
                        : "-"}
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-sm text-gray-500 bg-gray-50 border border-gray-100 rounded-lg p-4">
                  Chưa có chi tiết nguyên liệu cho combo này.
                </div>
              )}
            </div>
          </div>

          {/* Card 4: Pricing */}
          <div className="bg-white rounded-xl p-5 shadow-xs border border-gray-100">
            <h3 className="text-[15px] font-bold text-gray-800 mb-4 tracking-tight border-b border-gray-100 pb-3">
              Phân tích giá
            </h3>
            <div className="space-y-3.5 mb-4">
              <div className="flex justify-between items-center text-[13px]">
                <span className="text-gray-500 font-medium">Giá gốc</span>
                <span className="text-gray-600 font-semibold">
                  <span className="font-medium text-[12px] underline underline-offset-2 mr-px">
                    đ
                  </span>
                  {originalPrice.toLocaleString("vi-VN")}
                </span>
              </div>
              <div className="flex justify-between items-center text-[13px]">
                <span className="text-gray-500 font-medium">Giảm giá</span>
                <span className="text-[#ff4d4f] font-semibold">
                  -
                  <span className="font-medium text-[12px] underline underline-offset-2 mr-px">
                    đ
                  </span>
                  {discountValue.toLocaleString("vi-VN")}
                </span>
              </div>
            </div>

            <div className="border-t border-gray-100 pt-4 mb-3">
              <div className="flex justify-between items-center mb-3">
                <span className="text-gray-800 font-bold text-[14px]">
                  Tổng giá trị nguyên liệu
                </span>
                <span className="text-[#4CAF50] font-bold text-[20px] leading-none">
                  <span className="font-medium text-[15px] underline underline-offset-[3px] mr-px">
                    đ
                  </span>
                  {newPrice.toLocaleString("vi-VN")}
                </span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-gray-500 font-medium text-[13px]">
                  Lợi nhuận dự kiến
                </span>
                <span className="text-[#4CAF50] font-semibold text-[13px]">
                  Chưa có dữ liệu
                </span>
              </div>
            </div>
          </div>

          {/* Card 5: AI Explanation */}
          <div className="bg-white rounded-xl p-5 shadow-xs border border-gray-100">
            <div className="flex items-center gap-2.5 mb-5 border-b border-gray-100 pb-3">
              <div className="bg-green-50 w-7 h-7 flex items-center justify-center rounded-full text-[#4CAF50] border border-green-100">
                <SiProbot className="text-[14px]" />
              </div>
              <h3 className="text-[15px] font-bold text-gray-800 tracking-tight">
                Giải thích từ AI
              </h3>
            </div>

            <div className="space-y-2.5">
              <div className="bg-[#f8f9fa] rounded-lg p-3.5 flex gap-3.5 items-start">
                <FaBoxOpen className="text-[#4CAF50] text-[14px] mt-0.5 shrink-0" />
                <div>
                  <div className="font-bold text-[13px] text-gray-800 mb-1">
                    Tóm tắt đề xuất
                  </div>
                  <div className="text-[12px] text-gray-500 font-normal leading-[1.6]">
                    {combo.aiReason ||
                      "AI chưa cung cấp giải thích cho combo này."}
                  </div>
                </div>
              </div>

              <div className="bg-[#f8f9fa] rounded-lg p-3.5 flex gap-3.5 items-start">
                <FaChartLine className="text-[#4CAF50] text-[14px] mt-0.5 shrink-0" />
                <div>
                  <div className="font-bold text-[13px] text-gray-800 mb-1">
                    Chỉ số mô hình
                  </div>
                  <div className="text-[12px] text-gray-500 font-normal leading-[1.6]">
                    Độ tin cậy: {combo.confidence || 0}% · Giảm giá:{" "}
                    {combo.discount || 0}%
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Bar Actions */}
        <div className="p-4 sm:px-5 sm:py-4 shrink-0 w-full flex gap-3 bg-[#f8f9fc]">
          <button
            onClick={onClose}
            className="flex-1 bg-white border border-gray-200 hover:bg-gray-50 text-gray-800 py-3 rounded-lg text-[14px] font-semibold transition-colors shadow-xs"
          >
            Chỉnh sửa
          </button>
          <button
            onClick={() => onAccept(combo.id)}
            className="flex-1 bg-[#4CAF50] hover:bg-[#43a047] text-white py-3 rounded-lg text-[14px] font-semibold flex items-center justify-center transition-colors shadow-xs"
          >
            Chấp nhận Combo
          </button>
        </div>
      </div>
    </div>
  );
}
