import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Zap, Target, ShieldCheck, Link as LinkIcon, Search } from 'lucide-react';

const Home = () => {
  const [url, setUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleAnalyze = (e) => {
    e.preventDefault();
    if (!url.trim()) return;
    
    setIsLoading(true);
    // Giả lập loading nhẹ trước khi chuyển trang
    setTimeout(() => {
      navigate(`/analyze?url=${encodeURIComponent(url)}`);
    }, 800);
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 font-sans selection:bg-primary-100 selection:text-primary-900">
      
      {/* Header / Navbar */}
      <header className="px-8 py-6 flex justify-between items-center border-b border-slate-200 bg-white">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-primary-600 flex items-center justify-center text-white font-bold text-xl">S</div>
          <span className="font-bold text-xl text-slate-900 tracking-tight">ShoppingSupport</span>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-grow flex flex-col items-center justify-center px-4 py-16">
        
        <div className="max-w-5xl w-full text-center mb-12">
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-extrabold text-slate-900 tracking-tight mb-6 leading-tight">
            <span className="text-primary-600">Shopping Support System</span>
          </h1>
          <p className="text-lg text-slate-500 mb-10 max-w-2xl mx-auto leading-relaxed">
            Hệ thống hỗ trợ đưa quyết định mua sắm thông minh hơn.
          </p>

          <form onSubmit={handleAnalyze} className="max-w-2xl mx-auto relative group">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <LinkIcon className="h-5 w-5 text-slate-400 group-focus-within:text-primary-500 transition-colors" />
            </div>
            <input
              type="text"
              className="block w-full pl-12 pr-32 py-4 text-base border-slate-200 border rounded-xl bg-white text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-shadow shadow-sm"
              placeholder="Dán link sản phẩm vào đây..."
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              required
            />
            <button
              type="submit"
              disabled={isLoading}
              className="absolute inset-y-2 right-2 flex items-center gap-2 bg-primary-600 hover:bg-primary-700 text-white px-6 py-2 rounded-lg font-medium transition-colors disabled:opacity-70 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  <span>Phân tích</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl w-full mt-12">
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-card hover:shadow-card-hover transition-shadow">
            <div className="w-12 h-12 bg-primary-50 rounded-lg flex items-center justify-center text-primary-600 mb-4">
              <Zap className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 mb-2">Tốc độ chớp nhoáng</h3>
            <p className="text-sm text-slate-500 leading-relaxed">
              Trích xuất và tổng hợp hàng ngàn nhận xét từ người dùng thực chỉ trong vài giây đồng hồ.
            </p>
          </div>
          
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-card hover:shadow-card-hover transition-shadow">
            <div className="w-12 h-12 bg-emerald-50 rounded-lg flex items-center justify-center text-emerald-600 mb-4">
              <Target className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 mb-2">Độ chuẩn xác cao</h3>
            <p className="text-sm text-slate-500 leading-relaxed">
              Mô hình AI chuyên biệt (PhoBERT) phân loại cảm xúc theo từng khía cạnh: Chất lượng, Giá, Giao hàng.
            </p>
          </div>

          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-card hover:shadow-card-hover transition-shadow">
            <div className="w-12 h-12 bg-amber-50 rounded-lg flex items-center justify-center text-amber-600 mb-4">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 mb-2">Lọc nhiễu hiệu quả</h3>
            <p className="text-sm text-slate-500 leading-relaxed">
              Tự động loại bỏ các bình luận spam, seeding ảo để mang lại góc nhìn khách quan và trung thực nhất.
            </p>
          </div>
        </div>

      </main>

      <footer className="text-center py-8 text-sm text-slate-400">
        &copy; 2026 Shopping Support System. All rights reserved.
      </footer>
    </div>
  );
};

export default Home;
