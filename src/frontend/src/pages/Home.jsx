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
    setTimeout(() => {
      navigate(`/analyze?url=${encodeURIComponent(url)}`);
    }, 800);
  };

  return (
    <div className="min-h-screen flex flex-col bg-background font-sans">

      {/* Header */}
      <header className="px-6 md:px-8 py-5 flex items-center border-b border-border bg-surface/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-primary-600 flex items-center justify-center text-white font-bold text-lg tracking-tight">S</div>
          <span className="font-bold text-lg text-text-primary tracking-tight">ShoppingSupport</span>
        </div>
      </header>

      {/* Hero */}
      <main className="flex-grow flex flex-col items-center justify-center px-4 py-12 md:py-20">
        <div className="max-w-4xl w-full text-center">
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-extrabold text-text-primary tracking-tight mb-4 leading-[1.1] animate-fade-in-up">
            Shopping Support System
          </h1>

          {/* Decorative rule */}
          <div className="flex items-center justify-center gap-3 mb-6 animate-fade-in-up-delay-1">
            <div className="h-px w-12 bg-primary-600/40"></div>
            <div className="w-1.5 h-1.5 rounded-full bg-primary-600"></div>
            <div className="h-px w-12 bg-primary-600/40"></div>
          </div>

          <p className="text-lg text-text-secondary mb-10 max-w-xl mx-auto leading-relaxed animate-fade-in-up-delay-1">
            Hệ thống hỗ trợ đưa quyết định mua sắm thông minh hơn.
            Phân tích cảm xúc đa khía cạnh bằng AI.
          </p>

          {/* Search Bar */}
          <form onSubmit={handleAnalyze} className="max-w-2xl mx-auto relative group animate-fade-in-up-delay-2">
            <div className="absolute inset-y-0 left-0 pl-5 flex items-center pointer-events-none">
              <LinkIcon className="h-5 w-5 text-text-secondary group-focus-within:text-primary-600 transition-colors" />
            </div>
            <input
              type="text"
              className="block w-full pl-14 pr-36 py-4.5 text-base border-border border rounded-xl bg-surface text-text-primary placeholder:text-text-secondary/60 focus:outline-none focus:ring-2 focus:ring-primary-600/30 focus:border-primary-600 transition-all shadow-card"
              placeholder="Dán link sản phẩm Shopee, Lazada, Tiki..."
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              required
            />
            <button
              type="submit"
              disabled={isLoading}
              className="absolute inset-y-2.5 right-2.5 flex items-center gap-2 bg-primary-600 hover:bg-primary-700 text-white px-6 py-2.5 rounded-lg font-semibold text-sm transition-all hover:shadow-lg disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
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
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 max-w-4xl w-full mt-16">
          <div className="bg-surface p-6 rounded-xl border border-border shadow-card hover:shadow-card-hover transition-all duration-300 animate-fade-in-up-delay-1 border-l-4 border-l-primary-600">
            <div className="w-11 h-11 bg-primary-50 rounded-lg flex items-center justify-center text-primary-600 mb-4">
              <Zap className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-text-primary mb-2">Tốc độ chớp nhoáng</h3>
            <p className="text-sm text-text-secondary leading-relaxed">
              Trích xuất và tổng hợp hàng ngàn nhận xét từ người dùng thực chỉ trong vài giây đồng hồ.
            </p>
          </div>

          <div className="bg-surface p-6 rounded-xl border border-border shadow-card hover:shadow-card-hover transition-all duration-300 animate-fade-in-up-delay-2 border-l-4 border-l-positive">
            <div className="w-11 h-11 bg-amber-50 rounded-lg flex items-center justify-center text-positive mb-4">
              <Target className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-text-primary mb-2">Độ chuẩn xác cao</h3>
            <p className="text-sm text-text-secondary leading-relaxed">
              Mô hình AI chuyên biệt (PhoBERT) phân loại cảm xúc theo từng khía cạnh: Chất lượng, Giá, Giao hàng.
            </p>
          </div>

          <div className="bg-surface p-6 rounded-xl border border-border shadow-card hover:shadow-card-hover transition-all duration-300 animate-fade-in-up-delay-3 border-l-4 border-l-neutral-sentiment">
            <div className="w-11 h-11 bg-teal-50 rounded-lg flex items-center justify-center text-neutral-sentiment mb-4">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-text-primary mb-2">Lọc nhiễu hiệu quả</h3>
            <p className="text-sm text-text-secondary leading-relaxed">
              Tự động loại bỏ các bình luận spam, seeding ảo để mang lại góc nhìn khách quan và trung thực nhất.
            </p>
          </div>
        </div>
      </main>

      <footer className="text-center py-6 text-sm text-text-secondary border-t border-border">
        &copy; 2026 Shopping Support System. All rights reserved.
      </footer>
    </div>
  );
};

export default Home;
