import React, { useState } from 'react';
import { Upload, FileSpreadsheet, CheckCircle2, AlertCircle, X, Loader2 } from 'lucide-react';
import { importAudienceFile } from '../services/api';

export default function AudienceImportModal({ isOpen, onClose, audience, onImportSuccess }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  if (!isOpen || !audience) return null;

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
      setResult(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Пожалуйста, выберите файл .csv или .xlsx');
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await importAudienceFile(audience.id, file);
      setResult(res);
      if (onImportSuccess) {
        onImportSuccess(res);
      }
    } catch (err) {
      setError(err.message || 'Ошибка импорта файла');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setResult(null);
    setError(null);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in">
      <div className="bg-[#0f172a] border border-slate-700/80 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden flex flex-col">
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
          <div className="flex items-center space-x-2">
            <div className="p-2 rounded-xl bg-blue-500/10 text-blue-400">
              <FileSpreadsheet className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-slate-100">Импорт контактов в аудиторию</h3>
              <p className="text-xs text-slate-400 truncate max-w-xs">{audience.name}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 p-1.5 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-5">
          {!result ? (
            <>
              {/* Drag and Drop Box */}
              <div
                className={`border-2 border-dashed rounded-xl p-8 text-center transition-all ${
                  file
                    ? 'border-blue-500/50 bg-blue-500/5'
                    : 'border-slate-700 hover:border-slate-600 bg-slate-900/40'
                }`}
              >
                <input
                  type="file"
                  id="audience-file-input"
                  accept=".csv, .xlsx, .xls"
                  onChange={handleFileChange}
                  className="hidden"
                />
                <label
                  htmlFor="audience-file-input"
                  className="cursor-pointer flex flex-col items-center space-y-3"
                >
                  <div className="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center text-blue-400">
                    <Upload className="w-6 h-6" />
                  </div>
                  <div>
                    <span className="text-sm font-medium text-blue-400 hover:underline">
                      {file ? file.name : 'Выберите файл для загрузки'}
                    </span>
                    <p className="text-xs text-slate-400 mt-1">Поддерживаются форматы .CSV, .XLSX</p>
                  </div>
                  {file && (
                    <span className="text-[11px] px-2.5 py-1 rounded-full bg-blue-500/20 text-blue-300 font-mono">
                      {(file.size / 1024).toFixed(1)} KB
                    </span>
                  )}
                </label>
              </div>

              {/* Format Hints */}
              <div className="bg-slate-900/80 rounded-xl p-3.5 border border-slate-800/80 text-xs text-slate-400 space-y-1.5">
                <span className="font-semibold text-slate-300">💡 Автоопределение колонок:</span>
                <p>Колонки <code>company_name</code> (или «название»), <code>email</code>, <code>phone</code>, <code>website</code>, <code>city</code> определятся автоматически. Дополнительные поля сохранятся в карточку лида для ИИ.</p>
              </div>

              {error && (
                <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-center space-x-2 text-rose-400 text-xs">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{error}</span>
                </div>
              )}
            </>
          ) : (
            /* Success Feedback */
            <div className="py-6 text-center space-y-4">
              <div className="w-14 h-14 rounded-full bg-emerald-500/10 text-emerald-400 mx-auto flex items-center justify-center">
                <CheckCircle2 className="w-8 h-8" />
              </div>
              <div>
                <h4 className="text-lg font-bold text-slate-100">Импорт успешно завершен!</h4>
                <p className="text-xs text-slate-400 mt-1">Контакты добавлены в базу аудитории</p>
              </div>

              <div className="grid grid-cols-2 gap-3 max-w-xs mx-auto text-left">
                <div className="p-3 bg-slate-900 rounded-xl border border-slate-800">
                  <span className="text-[11px] text-slate-400 block">Добавлено новых</span>
                  <span className="text-xl font-bold text-emerald-400 font-mono">
                    +{result.imported || 0}
                  </span>
                </div>
                <div className="p-3 bg-slate-900 rounded-xl border border-slate-800">
                  <span className="text-[11px] text-slate-400 block">Пропущено дублей</span>
                  <span className="text-xl font-bold text-amber-400 font-mono">
                    {result.duplicates_skipped || 0}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-800 bg-slate-900/40 flex items-center justify-end space-x-3">
          {!result ? (
            <>
              <button
                onClick={onClose}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
              >
                Отмена
              </button>
              <button
                onClick={handleUpload}
                disabled={!file || loading}
                className="px-5 py-2 rounded-xl text-xs font-semibold text-white bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:pointer-events-none flex items-center space-x-1.5 shadow-lg shadow-blue-600/20"
              >
                {loading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                <span>{loading ? 'Импортируем...' : 'Импортировать'}</span>
              </button>
            </>
          ) : (
            <button
              onClick={onClose}
              className="px-5 py-2 rounded-xl text-xs font-semibold text-white bg-blue-600 hover:bg-blue-500"
            >
              Готово
            </button>
          )}
        </div>

      </div>
    </div>
  );
}
