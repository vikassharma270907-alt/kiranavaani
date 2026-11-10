import React, { useRef } from "react";
import { Printer, Download, X, QrCode, Sparkles, CheckCircle2, ShieldCheck, Receipt } from "lucide-react";
import { CartItem } from "./ShoppingCart";

interface ThermalReceiptModalProps {
  isOpen: boolean;
  onClose: () => void;
  items: CartItem[];
  subtotal: number;
  total: number;
  customerName?: string;
  paymentMode?: string;
}

export const ThermalReceiptModal: React.FC<ThermalReceiptModalProps> = ({
  isOpen,
  onClose,
  items,
  subtotal,
  total,
  customerName = "Sharma Ji (शर्मा जी)",
  paymentMode = "UPI"
}) => {
  const receiptRef = useRef<HTMLDivElement | null>(null);

  if (!isOpen) return null;

  const now = new Date();
  const dateStr = now.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
  const timeStr = now.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
  const receiptNo = `KRN-${now.getFullYear().toString().slice(-2)}${(now.getMonth() + 1).toString().padStart(2, "0")}-${Math.floor(1000 + Math.random() * 9000)}`;

  const cgst = (total * 0.025).toFixed(2);
  const sgst = (total * 0.025).toFixed(2);
  const savings = (total * 0.08).toFixed(2);
  const upiQrString = `upi://pay?pa=guptakirana@okaxis&pn=GuptaKirana&am=${total}&cu=INR&tn=${receiptNo}`;

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-sm bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl flex flex-col max-h-[92vh] overflow-hidden">
        {/* Header Bar */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-slate-800 bg-slate-950/80">
          <div className="flex items-center gap-2">
            <Receipt className="w-5 h-5 text-teal-400" />
            <h3 className="text-sm font-semibold text-white tracking-wide">
              58mm Kirana Thermal POS Receipt
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Receipt Body */}
        <div className="overflow-y-auto p-4 flex justify-center bg-slate-950/60">
          {/* Authentic 58mm Thermal Receipt Styling */}
          <div
            ref={receiptRef}
            className="w-full bg-[#fcfbf9] text-slate-900 font-mono text-[11px] leading-tight p-4 shadow-lg rounded-sm border-t-4 border-dashed border-slate-400 print:shadow-none print:border-none print:m-0 print:p-2"
            style={{
              fontFamily: "'Courier New', Courier, monospace",
              backgroundImage: "linear-gradient(rgba(0,0,0,0.01) 1px, transparent 1px)",
              backgroundSize: "100% 4px"
            }}
          >
            {/* Store Header */}
            <div className="text-center pb-2 border-b border-dashed border-slate-400 space-y-0.5">
              <div className="text-xs font-black tracking-wider text-black">
                GUPTA KIRANA & GENERAL STORE
              </div>
              <div className="text-[10px] text-slate-600 font-sans">
                शुद्ध राशन • विश्वास का प्रतीक • प्रो. रमेश गुप्ता
              </div>
              <div className="text-[9px] text-slate-600">
                दुकान नं. 4, मुख्य बाज़ार, दिल्ली - 110001
              </div>
              <div className="text-[9px] text-slate-600">
                फ़ोन: +91 98111-23456 • FSSAI: 13324999000182
              </div>
              <div className="text-[9px] text-slate-600 font-bold">
                GSTIN: 07AAAAA0000A1Z5 (Composition)
              </div>
            </div>

            {/* Receipt Meta */}
            <div className="py-2 border-b border-dashed border-slate-300 text-[10px] space-y-0.5">
              <div className="flex justify-between">
                <span>रसीद / BILL NO:</span>
                <span className="font-bold">{receiptNo}</span>
              </div>
              <div className="flex justify-between">
                <span>दिनांक / DATE:</span>
                <span>{dateStr} {timeStr}</span>
              </div>
              <div className="flex justify-between">
                <span>ग्राहक / CUSTOMER:</span>
                <span className="font-bold">{customerName}</span>
              </div>
              <div className="flex justify-between">
                <span>भुगतान / MODE:</span>
                <span className="font-bold text-teal-800">{paymentMode.toUpperCase()}</span>
              </div>
            </div>

            {/* Line Items Table */}
            <div className="py-2 border-b border-dashed border-slate-400">
              <div className="flex justify-between font-bold text-[10px] border-b border-slate-300 pb-1 mb-1">
                <span className="w-1/2">सामान / ITEM</span>
                <span className="w-1/6 text-center">मात्रा</span>
                <span className="w-1/6 text-right">दर</span>
                <span className="w-1/6 text-right">रुपये</span>
              </div>
              <div className="space-y-1.5">
                {items.map((item, idx) => (
                  <div key={item.sku_id || idx} className="space-y-0.5">
                    <div className="font-bold text-[10.5px] text-black">
                      {item.name_en}
                    </div>
                    <div className="flex justify-between text-[10px] text-slate-700">
                      <span className="font-sans text-[9.5px] text-slate-600 pl-1">
                        {item.name_hi}
                      </span>
                      <span>{item.quantity} {item.unit}</span>
                      <span>@{item.unit_price}</span>
                      <span className="font-bold text-black">₹{item.line_total.toFixed(2)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Tax & Totals Breakdown */}
            <div className="py-2 border-b border-dashed border-slate-400 text-[10.5px] space-y-1">
              <div className="flex justify-between">
                <span>उप-योग / SUBTOTAL:</span>
                <span>₹{subtotal.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-[9.5px] text-slate-600">
                <span>CGST (2.5%):</span>
                <span>₹{cgst}</span>
              </div>
              <div className="flex justify-between text-[9.5px] text-slate-600">
                <span>SGST (2.5%):</span>
                <span>₹{sgst}</span>
              </div>
              <div className="flex justify-between text-[9.5px] text-emerald-800 font-bold">
                <span>आपकी कुल बचत / SAVINGS:</span>
                <span>-₹{savings}</span>
              </div>
              <div className="flex justify-between text-xs font-black text-black pt-1 border-t border-slate-300">
                <span>कुल योग / TOTAL:</span>
                <span className="text-sm">₹{total.toFixed(2)}</span>
              </div>
            </div>

            {/* Scan to Pay UPI Section */}
            <div className="py-3 text-center space-y-1.5 border-b border-dashed border-slate-400">
              <div className="text-[9.5px] font-bold text-slate-700 uppercase tracking-wider">
                Scan with Any UPI App to Pay
              </div>
              <div className="flex justify-center">
                <div className="p-2 bg-white border border-slate-300 rounded shadow-sm inline-block">
                  <img
                    src={`https://api.qrserver.com/v1/create-qr-code/?size=110x110&data=${encodeURIComponent(upiQrString)}`}
                    alt="UPI Payment QR"
                    className="w-24 h-24 object-contain"
                  />
                </div>
              </div>
              <div className="text-[8.5px] text-slate-500 font-mono">
                VPA: guptakirana@okaxis
              </div>
            </div>

            {/* Footer / Thank You Note */}
            <div className="pt-2 text-center text-[9px] text-slate-600 space-y-0.5">
              <div className="font-bold">🙏 आपके आगमन के लिए धन्यवाद! 🙏</div>
              <div>किरानावाणी AI वॉयस कॉमर्स द्वारा संचालित</div>
              <div className="text-[8px] text-slate-400 tracking-tighter">
                POWERED BY GNANI.AI PRISMA v3.0 & TIMBRE v2.5
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="p-3.5 border-t border-slate-800 bg-slate-950/90 flex items-center justify-between gap-3">
          <button
            onClick={onClose}
            className="px-3.5 py-2 text-xs font-medium text-slate-400 hover:text-white bg-slate-800/80 hover:bg-slate-800 rounded-lg transition"
          >
            Close
          </button>
          <div className="flex items-center gap-2">
            <button
              onClick={handlePrint}
              className="px-4 py-2 text-xs font-semibold text-white bg-teal-600 hover:bg-teal-500 rounded-lg shadow-md hover:shadow-teal-500/20 flex items-center gap-1.5 transition"
            >
              <Printer className="w-3.5 h-3.5" />
              Print 58mm Thermal Bill
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
