import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
  ArrowLeft, MessageSquare, BarChart2, ShieldCheck,
  ThumbsUp, ThumbsDown, Package, Truck, HeadphonesIcon, AlertCircle
} from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

const Dashboard = () => {
  const [searchParams] = useSearchParams();
  const url = searchParams.get('url');
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [data, setData] = useState(null);
  const [activeTab, setActiveTab] = useState('Quality');

  useEffect(() => {
    if (!url) {
      navigate('/');
      return;
    }

    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await axios.post('http://localhost:8000/api/analyze', { url });
        setData(response.data);
      } catch (err) {
        setError('Có lỗi xảy ra khi kết nối với AI Server. Vui lòng thử lại sau.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [url, navigate]);

  // Loading State
  if (loading) {
    return (
      <div className="min-h-screen bg-background flex flex-col items-center justify-center px-4">
        <div className="w-14 h-14 border-4 border-primary-100 border-t-primary-600 rounded-full animate-spin mb-6"></div>
        <h2 className="text-xl font-bold text-text-primary mb-2">Đang phân tích dữ liệu...</h2>
        <p className="text-text-secondary text-sm max-w-md text-center">
          Hệ thống đang cào bình luận và sử dụng AI để đánh giá cảm xúc đa khía cạnh.
        </p>
        {/* Shimmer skeleton */}
        <div className="mt-8 w-full max-w-md space-y-3">
          <div className="h-4 rounded-full animate-shimmer"></div>
          <div className="h-4 rounded-full animate-shimmer w-5/6"></div>
          <div className="h-4 rounded-full animate-shimmer w-4/6"></div>
        </div>
      </div>
    );
  }

  // Error State
  if (error) {
    return (
      <div className="min-h-screen bg-background flex flex-col items-center justify-center px-4">
        <div className="bg-surface p-8 rounded-xl shadow-card border border-border max-w-md w-full text-center">
          <div className="w-16 h-16 bg-red-50 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-8 h-8 text-negative" />
          </div>
          <h2 className="text-xl font-bold text-text-primary mb-2">Thất bại!</h2>
          <p className="text-text-secondary mb-6 text-sm">{error}</p>
          <button
            onClick={() => navigate('/')}
            className="bg-primary-600 text-white px-6 py-2.5 rounded-lg font-semibold text-sm hover:bg-primary-700 transition-all w-full"
          >
            Quay lại trang chủ
          </button>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const { overview, aspects, product_info } = data;
  
  // Chuẩn bị dữ liệu cho biểu đồ Donut
  const getChartData = (aspectKey) => {
    const stats = aspects[aspectKey].stats;
    const result = [];
    if (stats['Khen'] > 0) result.push({ name: 'Khen', value: stats['Khen'], color: '#b45309' });
    if (stats['Bình thường'] > 0) result.push({ name: 'Bình thường', value: stats['Bình thường'], color: '#0d9488' });
    if (stats['Chê'] > 0) result.push({ name: 'Chê', value: stats['Chê'], color: '#be123c' });
    return result;
  };

  const chartData = getChartData(activeTab);
  const activeAspectData = aspects[activeTab];

  const aspectIcons = {
    'Quality': <Package className="w-4 h-4" />,
    'Price': <BarChart2 className="w-4 h-4" />,
    'Delivery': <Truck className="w-4 h-4" />,
    'Service': <HeadphonesIcon className="w-4 h-4" />
  };

  return (
    <div className="min-h-screen bg-background font-sans">

      {/* Top Bar */}
      <div className="bg-surface border-b border-border px-6 py-4 flex items-center gap-4 sticky top-0 z-10">
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-2 text-sm text-text-secondary hover:text-text-primary font-medium transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span className="hidden sm:inline">Về trang chủ</span>
        </button>
        <div className="h-5 w-px bg-border"></div>
        <h1 className="text-base font-bold text-text-primary tracking-tight">Báo cáo Phân tích</h1>
        <div className="ml-auto flex items-center gap-2 text-xs text-text-secondary bg-background px-3 py-1.5 rounded-lg border border-border max-w-xs overflow-hidden">
          <span className="font-medium shrink-0">Nguồn:</span>
          <a href={url} target="_blank" rel="noreferrer" className="text-primary-600 hover:underline truncate">
            {url}
          </a>
        </div>
      </div>

      {/* Main Content Area */}
      <main className="flex-grow p-4 md:p-8 overflow-y-auto w-full">
        
        {/* Header Title & Product Info */}
        <div className="mb-8">
          <div className="flex flex-col md:flex-row gap-8 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm items-center md:items-start">
            {product_info?.image && (
              <div className="w-48 h-48 md:w-64 md:h-64 shrink-0 rounded-xl overflow-hidden border border-slate-100 shadow-sm bg-slate-50 flex items-center justify-center">
                <img src={product_info.image} alt={product_info.name} className="max-w-full max-h-full object-contain" />
              </div>
            )}
            <div className="flex flex-col justify-center h-full py-2 w-full">
              <h1 className="text-2xl md:text-4xl font-extrabold text-slate-900 tracking-tight mb-4 leading-tight">
                {product_info?.name || "Báo cáo Phân tích Sản phẩm"}
              </h1>
              <div className="flex items-center gap-3">
                <span className="text-sm font-semibold text-slate-500 uppercase tracking-wider">Nguồn dữ liệu:</span>
                <a href={url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 bg-primary-50 text-primary-700 px-4 py-2 rounded-lg font-bold hover:bg-primary-100 transition-colors">
                  {url.includes('shopee') ? '🛍️ Shopee' : '📦 Tiki'}
                </a>
              </div>
            </div>
          </div>

          <div className="bg-surface p-6 rounded-xl border border-border shadow-card flex flex-col justify-between">
            <span className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-2">Số lượng đã quét</span>
            <div className="mt-1">
              <span className="text-4xl font-extrabold text-text-primary tracking-tight">{overview.total_analyzed_comments}</span>
              <span className="text-base font-medium text-text-secondary ml-2">bình luận</span>
            </div>
          </div>

          <div className="bg-surface p-6 rounded-xl border border-border shadow-card flex flex-col justify-between">
            <span className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-2">Tỷ lệ Khen / Chê</span>
            <div className="mt-1 flex items-end gap-3">
              <div className="flex items-baseline gap-1">
                <span className="text-4xl font-extrabold text-positive">{overview.total_khen}</span>
                <span className="text-sm text-text-secondary">khen</span>
              </div>
              <span className="text-2xl text-border font-light">/</span>
              <div className="flex items-baseline gap-1">
                <span className="text-4xl font-extrabold text-negative">{overview.total_che}</span>
                <span className="text-sm text-text-secondary">chê</span>
              </div>
            </div>
            {/* Mini bar indicator */}
            <div className="mt-3 h-2 rounded-full bg-background overflow-hidden flex">
              <div
                className="h-full bg-positive rounded-l-full transition-all duration-700"
                style={{ width: `${overview.total_khen + overview.total_che > 0 ? (overview.total_khen / (overview.total_khen + overview.total_che) * 100) : 50}%` }}
              ></div>
              <div
                className="h-full bg-negative rounded-r-full transition-all duration-700"
                style={{ width: `${overview.total_khen + overview.total_che > 0 ? (overview.total_che / (overview.total_khen + overview.total_che) * 100) : 50}%` }}
              ></div>
            </div>
          </div>
        </div>

        {/* Aspect Section */}
        <div className="mb-6 animate-fade-in-up-delay-1">
          <h2 className="text-lg font-bold text-text-primary mb-4">Chi tiết theo khía cạnh</h2>

          {/* Tabs */}
          <div className="flex overflow-x-auto pb-1 gap-2">
            {Object.keys(aspects).map((key) => (
              <button
                key={key}
                onClick={() => setActiveTab(key)}
                className={`flex items-center gap-2 px-5 py-2.5 font-medium text-sm transition-all whitespace-nowrap rounded-lg ${
                  activeTab === key
                    ? 'bg-primary-600 text-white shadow-sm'
                    : 'text-text-secondary hover:text-text-primary hover:bg-surface border border-border'
                }`}
              >
                {aspectIcons[key]} {aspects[key].name}
              </button>
            ))}
          </div>
        </div>

        {/* Tab Content */}
        <div className="bg-surface border border-border rounded-xl shadow-card overflow-hidden animate-fade-in-up-delay-2">

          {/* AI Summary — Gemini-generated */}
          <div className="relative bg-gradient-to-br from-primary-50/60 via-background to-primary-50/30 border-b border-border px-6 py-5">
            <div className="flex items-start gap-3.5">
              <div className="shrink-0 bg-primary-100 p-2 rounded-lg mt-0.5 shadow-sm">
                <ShieldCheck className="w-4 h-4 text-primary-600" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs font-bold text-primary-600 uppercase tracking-wider">Gemini AI nhận xét</span>
                  <span className="inline-block w-1.5 h-1.5 rounded-full bg-primary-400 animate-pulse"></span>
                </div>
                <p className="text-sm text-text-primary leading-relaxed font-medium" style={{ textIndent: '1.5em' }}>
                  {activeAspectData.summary}
                </p>
              </div>
            </div>
            {/* Decorative corner accent */}
            <div className="absolute top-0 right-0 w-16 h-16 overflow-hidden rounded-tr-xl pointer-events-none">
              <div className="absolute -top-8 -right-8 w-16 h-16 bg-primary-100/40 rotate-45"></div>
            </div>
          </div>

          <div className="flex flex-col lg:flex-row">
            {/* Chart */}
            <div className="w-full lg:w-2/5 p-6 border-b lg:border-b-0 lg:border-r border-border flex flex-col items-center justify-center min-h-[280px]">
              {chartData.length > 0 ? (
                <>
                  <h3 className="text-xs font-bold text-text-primary w-full text-center mb-4 uppercase tracking-wider">Phân bố cảm xúc</h3>
                  <div className="w-full h-56">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={chartData}
                          innerRadius={55}
                          outerRadius={85}
                          paddingAngle={3}
                          dataKey="value"
                          stroke="none"
                        >
                          {chartData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip
                          formatter={(value, name) => [`${value} bình luận`, name]}
                          contentStyle={{
                            borderRadius: '10px',
                            border: '1px solid #e7e0d8',
                            boxShadow: '0 4px 12px rgba(26, 26, 46, 0.08)',
                            fontSize: '13px',
                            fontFamily: '"Be Vietnam Pro", sans-serif'
                          }}
                        />
                        <Legend
                          verticalAlign="bottom"
                          height={36}
                          iconType="circle"
                          iconSize={8}
                          formatter={(value) => <span style={{ color: '#6b7280', fontSize: '12px', fontFamily: '"Be Vietnam Pro", sans-serif' }}>{value}</span>}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </>
              ) : (
                <div className="text-center text-text-secondary flex flex-col items-center">
                  <BarChart2 className="w-10 h-10 mb-2 opacity-20" />
                  <p className="text-sm">Không có dữ liệu cho khía cạnh này</p>
                </div>
              )}
            </div>

            {/* Comments */}
            <div className="w-full lg:w-3/5 p-6">
              <h3 className="text-xs font-bold text-text-primary mb-4 flex items-center gap-2 uppercase tracking-wider">
                <MessageSquare className="w-4 h-4 text-text-secondary" /> Ý kiến tiêu biểu
              </h3>

              <div className="space-y-5">

                {/* Positive */}
                {activeAspectData.highlights.positive.length > 0 && (
                  <div>
                    <div className="flex items-center gap-2 mb-3">
                      <div className="bg-amber-50 text-positive p-1.5 rounded-md">
                        <ThumbsUp className="w-3.5 h-3.5" />
                      </div>
                      <h4 className="text-sm font-semibold text-positive">Điểm khen</h4>
                    </div>
                    <div className="space-y-2">
                      {activeAspectData.highlights.positive.map((cmt, idx) => (
                        <div key={idx} className="bg-amber-50/40 border border-amber-100 border-l-4 border-l-positive rounded-lg p-3.5 text-sm text-text-primary shadow-sm leading-relaxed">
                          &ldquo;{cmt}&rdquo;
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Negative */}
                {activeAspectData.highlights.negative.length > 0 && (
                  <div>
                    <div className="flex items-center gap-2 mb-3">
                      <div className="bg-red-50 text-negative p-1.5 rounded-md">
                        <ThumbsDown className="w-3.5 h-3.5" />
                      </div>
                      <h4 className="text-sm font-semibold text-negative">Điểm chê</h4>
                    </div>
                    <div className="space-y-2">
                      {activeAspectData.highlights.negative.map((cmt, idx) => (
                        <div key={idx} className="bg-red-50/40 border border-red-100 border-l-4 border-l-negative rounded-lg p-3.5 text-sm text-text-primary shadow-sm leading-relaxed">
                          &ldquo;{cmt}&rdquo;
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Empty */}
                {activeAspectData.highlights.positive.length === 0 && activeAspectData.highlights.negative.length === 0 && (
                  <div className="text-center py-10 text-text-secondary bg-background rounded-lg border border-border border-dashed text-sm">
                    Chưa có bình luận nổi bật nào.
                  </div>
                )}

              </div>
            </div>
          </div>
        </div>

      </main>
    </div>
  );
};

export default Dashboard;
