import React, { useState, useEffect } from 'react';
import { 
  Package, Plus, Sparkles, Trash2, Edit3, ArrowRight, 
  Target, CheckCircle2, AlertCircle, RefreshCw, Layers, ShieldCheck
} from 'lucide-react';
import { fetchProducts, deleteProduct } from '../services/api';
import CreateProductModal from './CreateProductModal';

export default function ProductsHub({ currentProjectId, onLaunchFunnelStudio }) {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [actionNotice, setActionNotice] = useState(null);

  const loadProducts = async () => {
    if (!currentProjectId) return;
    setLoading(true);
    try {
      const data = await fetchProducts(currentProjectId);
      setProducts(data || []);
    } catch (err) {
      console.error('Failed to load products:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProducts();
  }, [currentProjectId]);

  const handleDelete = async (prod) => {
    if (!window.confirm(`Вы уверены, что хотите удалить продукт "${prod.name}"?`)) {
      return;
    }
    try {
      await deleteProduct(prod.id);
      setProducts(prev => prev.filter(p => p.id !== prod.id));
      showNotice(`Продукт "${prod.name}" удален`, 'success');
    } catch (err) {
      showNotice(err.message || 'Ошибка удаления продукта', 'error');
    }
  };

  const showNotice = (msg, type = 'info') => {
    setActionNotice({ msg, type });
    setTimeout(() => setActionNotice(null), 4000);
  };

  return (
    <div className="space-y-6">
      
      {/* Header Banner */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 rounded-2xl bg-purple-600/10 border border-purple-500/20 text-purple-400 flex items-center justify-center">
              <Package className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-100">Продукты & Офферы</h2>
              <p className="text-xs text-slate-400">
                База знаний о ваших продуктах и услугах. Используется ИИ для генерации продающих персонализированных цепочек писем.
              </p>
            </div>
          </div>

          <button
            onClick={() => { setEditingProduct(null); setIsModalOpen(true); }}
            className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-purple-600 hover:bg-purple-500 shadow-lg shadow-purple-600/25 flex items-center space-x-2 transition-all transform hover:-translate-y-0.5"
          >
            <Plus className="w-4 h-4" />
            <span>Добавить продукт</span>
          </button>
        </div>
      </div>

      {/* Notice Toast */}
      {actionNotice && (
        <div className={`p-4 rounded-xl flex items-center space-x-3 text-xs font-medium border animate-fade-in ${
          actionNotice.type === 'error'
            ? 'bg-rose-500/10 text-rose-300 border-rose-500/30'
            : 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
        }`}>
          {actionNotice.type === 'error' ? <AlertCircle className="w-4 h-4" /> : <CheckCircle2 className="w-4 h-4" />}
          <span>{actionNotice.msg}</span>
        </div>
      )}

      {/* Products Grid */}
      {loading ? (
        <div className="p-12 text-center text-slate-400">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-purple-400" />
          <p className="text-xs">Загрузка продуктов...</p>
        </div>
      ) : products.length === 0 ? (
        <div className="border border-dashed border-slate-800 rounded-2xl p-12 text-center space-y-4 bg-slate-900/20">
          <div className="w-14 h-14 rounded-full bg-slate-800 flex items-center justify-center mx-auto text-slate-500">
            <Package className="w-7 h-7" />
          </div>
          <div>
            <h4 className="text-base font-semibold text-slate-200">В этом проекте пока нет продуктов</h4>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
              Опишите ваш продукт, его выгоды и боли клиента. На основе этих данных ИИ-копирайтер создаст идеальную воронку касаний.
            </p>
          </div>
          <button
            onClick={() => { setEditingProduct(null); setIsModalOpen(true); }}
            className="px-5 py-2.5 rounded-xl text-xs font-semibold text-white bg-purple-600 hover:bg-purple-500 transition-all inline-flex items-center space-x-2"
          >
            <Plus className="w-4 h-4" />
            <span>Добавить первый продукт</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {products.map((prod) => (
            <div
              key={prod.id}
              className="bg-slate-900/80 border border-slate-800 hover:border-slate-700/80 rounded-2xl p-5 flex flex-col justify-between transition-all hover:shadow-xl hover:shadow-black/40 group"
            >
              <div className="space-y-4">
                
                {/* Header */}
                <div className="flex items-start justify-between gap-2">
                  <div className="space-y-1">
                    <h3 className="text-base font-bold text-slate-100 group-hover:text-purple-300 transition-colors">
                      {prod.name}
                    </h3>
                    {prod.description && (
                      <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                        {prod.description}
                      </p>
                    )}
                  </div>
                  {prod.pricing_details && (
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-300 font-mono border border-purple-500/20 flex-shrink-0">
                      {prod.pricing_details}
                    </span>
                  )}
                </div>

                {/* Target ICP */}
                {prod.target_audience_icp && (
                  <div className="p-2.5 bg-slate-950/60 rounded-xl border border-slate-800/80 text-xs text-slate-300 flex items-center space-x-2">
                    <Target className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0" />
                    <span className="truncate"><strong className="text-slate-400">ICP:</strong> {prod.target_audience_icp}</span>
                  </div>
                )}

                {/* Pain Points Chips */}
                {prod.pain_points && prod.pain_points.length > 0 && (
                  <div className="space-y-1.5">
                    <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">
                      Боли клиента:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {prod.pain_points.slice(0, 3).map((pain, i) => (
                        <span key={i} className="text-[11px] px-2 py-0.5 rounded-lg bg-rose-500/10 text-rose-300 border border-rose-500/20 truncate max-w-[200px]">
                          {pain}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Value Props Chips */}
                {prod.value_props && prod.value_props.length > 0 && (
                  <div className="space-y-1.5">
                    <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">
                      УТП / Выгоды:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {prod.value_props.slice(0, 3).map((usp, i) => (
                        <span key={i} className="text-[11px] px-2 py-0.5 rounded-lg bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 truncate max-w-[200px]">
                          {usp}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* CTA */}
                {prod.target_action_cta && (
                  <div className="text-[11px] text-slate-400 pt-1">
                    <span className="text-slate-500">Цель касания (CTA):</span>{' '}
                    <span className="text-slate-200 font-medium">{prod.target_action_cta}</span>
                  </div>
                )}

              </div>

              {/* Bottom Actions */}
              <div className="pt-5 mt-5 border-t border-slate-800/80 space-y-2">
                <button
                  onClick={() => onLaunchFunnelStudio(prod.id)}
                  className="w-full px-3.5 py-2.5 rounded-xl text-xs font-semibold text-white bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 shadow-md shadow-purple-600/20 flex items-center justify-center space-x-2 transition-all transform hover:-translate-y-0.5"
                >
                  <Sparkles className="w-3.5 h-3.5 text-amber-300 animate-pulse" />
                  <span>Сгенерировать воронку ИИ</span>
                  <ArrowRight className="w-3.5 h-3.5 ml-1" />
                </button>

                <div className="flex items-center justify-end space-x-2 pt-1">
                  <button
                    onClick={() => { setEditingProduct(prod); setIsModalOpen(true); }}
                    className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors text-xs flex items-center space-x-1"
                  >
                    <Edit3 className="w-3.5 h-3.5" />
                    <span>Редактировать</span>
                  </button>

                  <button
                    onClick={() => handleDelete(prod)}
                    className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors"
                    title="Удалить продукт"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

            </div>
          ))}
        </div>
      )}

      {/* Modal */}
      <CreateProductModal
        isOpen={isModalOpen}
        onClose={() => { setIsModalOpen(false); setEditingProduct(null); }}
        projectId={currentProjectId}
        productToEdit={editingProduct}
        onProductSaved={() => {
          loadProducts();
          showNotice(editingProduct ? 'Продукт обновлен' : 'Новый продукт добавлен!', 'success');
        }}
      />

    </div>
  );
}
