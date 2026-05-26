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
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center">
        <div className="w-16 h-16 border-4 border-primary-100 border-t-primary-600 rounded-full animate-spin mb-6"></div>
        <h2 className="text-xl font-semibold text-slate-900 mb-2">Đang phân tích dữ liệu...</h2>
        <p className="text-slate-500 text-sm max-w-md text-center">Hệ thống đang cào bình luận và sử dụng AI để đánh giá cảm xúc đa khía cạnh.</p>
      </div>
    );
  }

  // Error State
  if (error) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center px-4">
        <div className="bg-white p-8 rounded-xl shadow-card border border-red-100 max-w-md w-full text-center">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-slate-900 mb-2">Thất bại!</h2>
          <p className="text-slate-500 mb-6">{error}</p>
          <button 
            onClick={() => navigate('/')}
            className="bg-slate-900 text-white px-6 py-2 rounded-lg font-medium hover:bg-slate-800 transition-colors w-full"
          >
            Quay lại trang chủ
          </button>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const { overview, aspects } = data;
  
  // Chuẩn bị dữ liệu cho biểu đồ Donut
  const getChartData = (aspectKey) => {
    const stats = aspects[aspectKey].stats;
    const result = [];
    if (stats['Khen'] > 0) result.push({ name: 'Khen', value: stats['Khen'], color: '#059669' }); // emerald
    if (stats['Bình thường'] > 0) result.push({ name: 'Bình thường', value: stats['Bình thường'], color: '#d97706' }); // amber
    if (stats['Chê'] > 0) result.push({ name: 'Chê', value: stats['Chê'], color: '#dc2626' }); // red
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
    <div className="min-h-screen bg-slate-50 flex flex-col md:flex-row font-sans">
      
      {/* Sidebar Navigation */}
      <aside className="w-full md:w-64 bg-white border-r border-slate-200 flex flex-col hidden md:flex h-screen sticky top-0">
        <div className="p-6 border-b border-slate-200 flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-primary-600 flex items-center justify-center text-white font-bold">S</div>
          <span className="font-bold text-lg text-slate-900 tracking-tight">ShoppingSupport</span>
        </div>
        
        <div className="flex-grow p-4 overflow-y-auto">
          <button 
            onClick={() => navigate('/')}
            className="flex items-center gap-2 text-sm text-slate-500 hover:text-slate-900 mb-8 font-medium transition-colors"
          >
            <ArrowLeft className="w-4 h-4" /> Về trang chủ
          </button>

          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4 ml-2">Kết quả phân tích</div>
          <nav className="space-y-1">
            <a href="#" className="flex items-center gap-3 px-3 py-2 bg-primary-50 text-primary-700 rounded-lg font-medium">
              <BarChart2 className="w-5 h-5" /> Tổng quan
            </a>
            <a href="#" className="flex items-center gap-3 px-3 py-2 text-slate-600 hover:bg-slate-50 rounded-lg font-medium transition-colors">
              <MessageSquare className="w-5 h-5" /> Lịch sử quét
            </a>
          </nav>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-grow p-4 md:p-8 overflow-y-auto w-full">
        
        {/* Header Title */}
        <div className="mb-8">
          <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight mb-2">Báo cáo Phân tích Sản phẩm</h1>
          <div className="flex items-center gap-2 text-sm text-slate-500 bg-white px-4 py-2 rounded-lg border border-slate-200 shadow-sm inline-flex max-w-full overflow-hidden">
            <span className="font-medium shrink-0">Nguồn:</span>
            <a href={url} target="_blank" rel="noreferrer" className="text-primary-600 hover:underline truncate">
              {url}
            </a>
          </div>
        </div>

        {/* 3 Metric Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-card flex flex-col justify-between">
            <span className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-1">Khuyến nghị AI</span>
            <div className="text-2xl font-bold text-slate-900 mt-2" dangerouslySetInnerHTML={{__html: overview.final_verdict}} />
          </div>
          
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-card flex flex-col justify-between">
            <span className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-1">Số lượng đã quét</span>
            <div className="text-4xl font-extrabold text-slate-900 mt-2 tracking-tight">
              {overview.total_analyzed_comments} <span className="text-lg font-medium text-slate-400">bình luận</span>
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-card flex flex-col justify-between">
            <span className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-1">Tỷ lệ Khen / Chê</span>
            <div className="text-4xl font-extrabold mt-2 tracking-tight">
              <span className="text-emerald-600">{overview.total_khen}</span>
              <span className="text-slate-300 mx-2">/</span>
              <span className="text-red-600">{overview.total_che}</span>
            </div>
          </div>
        </div>

        {/* Khía cạnh phân tích */}
        <div className="mb-4">
          <h2 className="text-lg font-bold text-slate-900 mb-4">Chi tiết theo khía cạnh</h2>
          
          {/* Tabs - Minimalist Pills */}
          <div className="flex overflow-x-auto pb-2 gap-2 border-b border-slate-200">
            {Object.keys(aspects).map((key) => (
              <button
                key={key}
                onClick={() => setActiveTab(key)}
                className={`flex items-center gap-2 px-5 py-3 font-medium text-sm transition-all whitespace-nowrap border-b-2 ${
                  activeTab === key 
                    ? 'border-primary-600 text-primary-700 bg-primary-50 rounded-t-lg' 
                    : 'border-transparent text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-t-lg'
                }`}
              >
                {aspectIcons[key]} {aspects[key].name}
              </button>
            ))}
          </div>
        </div>

        {/* Tab Content (Split Layout: Chart | Comments) */}
        <div className="bg-white border border-slate-200 rounded-xl shadow-card overflow-hidden">
          
          {/* AI Summary Banner */}
          <div className="bg-slate-50 border-b border-slate-200 px-6 py-4 flex items-start gap-3">
            <div className="bg-white p-1 rounded-md shadow-sm border border-slate-200 mt-0.5">
              <ShieldCheck className="w-5 h-5 text-primary-600" />
            </div>
            <div>
              <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-0.5">AI NHẬN XÉT</div>
              <div className="text-sm text-slate-700 font-medium">{activeAspectData.summary}</div>
            </div>
          </div>

          <div className="flex flex-col lg:flex-row">
            {/* Chart Area */}
            <div className="w-full lg:w-2/5 p-6 border-b lg:border-b-0 lg:border-r border-slate-200 flex flex-col items-center justify-center min-h-[300px]">
              {chartData.length > 0 ? (
                <>
                  <h3 className="text-sm font-bold text-slate-900 w-full text-center mb-4 uppercase tracking-wider">Phân bố cảm xúc</h3>
                  <div className="w-full h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={chartData}
                          innerRadius={60}
                          outerRadius={90}
                          paddingAngle={2}
                          dataKey="value"
                        >
                          {chartData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} stroke="none" />
                          ))}
                        </Pie>
                        <Tooltip 
                          formatter={(value, name) => [`${value} bình luận`, name]}
                          contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}
                        />
                        <Legend verticalAlign="bottom" height={36} iconType="circle" />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </>
              ) : (
                <div className="text-center text-slate-400 flex flex-col items-center">
                  <BarChart2 className="w-12 h-12 mb-2 opacity-20" />
                  <p>Không có dữ liệu cho khía cạnh này</p>
                </div>
              )}
            </div>

            {/* Comments Area */}
            <div className="w-full lg:w-3/5 p-6 bg-slate-50/50">
              <h3 className="text-sm font-bold text-slate-900 mb-4 flex items-center gap-2 uppercase tracking-wider">
                <MessageSquare className="w-4 h-4 text-slate-400" /> Ý kiến tiêu biểu
              </h3>
              
              <div className="space-y-6">
                
                {/* Positive Comments */}
                {activeAspectData.highlights.positive.length > 0 && (
                  <div>
                    <div className="flex items-center gap-2 mb-3">
                      <div className="bg-emerald-100 text-emerald-700 p-1 rounded">
                        <ThumbsUp className="w-3 h-3" />
                      </div>
                      <h4 className="text-sm font-semibold text-emerald-800">Điểm khen</h4>
                    </div>
                    <div className="space-y-2">
                      {activeAspectData.highlights.positive.map((cmt, idx) => (
                        <div key={idx} className="bg-white border border-emerald-100 border-l-4 border-l-emerald-500 rounded-lg p-3 text-sm text-slate-700 shadow-sm leading-relaxed">
                          "{cmt}"
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Negative Comments */}
                {activeAspectData.highlights.negative.length > 0 && (
                  <div>
                    <div className="flex items-center gap-2 mb-3">
                      <div className="bg-red-100 text-red-700 p-1 rounded">
                        <ThumbsDown className="w-3 h-3" />
                      </div>
                      <h4 className="text-sm font-semibold text-red-800">Điểm chê</h4>
                    </div>
                    <div className="space-y-2">
                      {activeAspectData.highlights.negative.map((cmt, idx) => (
                        <div key={idx} className="bg-white border border-red-100 border-l-4 border-l-red-500 rounded-lg p-3 text-sm text-slate-700 shadow-sm leading-relaxed">
                          "{cmt}"
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Empty State */}
                {activeAspectData.highlights.positive.length === 0 && activeAspectData.highlights.negative.length === 0 && (
                  <div className="text-center py-8 text-slate-400 bg-white rounded-lg border border-slate-200 border-dashed">
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
