import React, { useState, useEffect, useRef } from 'react';
import { UploadCloud, Search, Database, FileSpreadsheet, AlertCircle, FileJson, Loader2 } from 'lucide-react';

export function DatasetExplorer() {
  const [datasets, setDatasets] = useState([]);
  const [selectedDataset, setSelectedDataset] = useState(null);
  const [keyword, setKeyword] = useState('');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchDatasets();
  }, []);

  const fetchDatasets = async () => {
    try {
      const res = await fetch('/api/datasets');
      const json = await res.json();
      setDatasets(json.datasets || []);
    } catch (err) {
      console.error('Failed to fetch datasets:', err);
    }
  };

  const handleSearch = async (pageNum = 1) => {
    if (!selectedDataset) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/datasets/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dataset_id: selectedDataset,
          keyword: keyword,
          page: pageNum,
          page_size: 50
        })
      });
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Failed to search dataset');
      }
      const json = await res.json();
      setData(json);
      setPage(json.page);
      setTotalPages(json.total_pages);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedDataset) {
      handleSearch(1);
    } else {
      setData(null);
    }
  }, [selectedDataset]);

  const handleFileUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    setUploading(true);
    setError(null);
    try {
      const res = await fetch('/api/datasets/upload', {
        method: 'POST',
        body: formData
      });
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Upload failed');
      }
      await fetchDatasets();
      setSelectedDataset(file.name);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const renderTable = () => {
    if (!data || !data.columns) return null;
    if (data.data.length === 0) {
      return (
        <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-muted)' }}>
          No records found matching "{keyword}".
        </div>
      );
    }

    return (
      <div style={{ overflowX: 'auto', borderRadius: '4px', border: '1px solid var(--border)', background: 'var(--bg-elevated)', marginTop: '1rem' }}>
        <table style={{ width: '100%', fontSize: '0.875rem', textAlign: 'left', borderCollapse: 'collapse', color: 'var(--text-primary)' }}>
          <thead style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', textTransform: 'uppercase', background: 'var(--bg-hover)', borderBottom: '1px solid var(--border)' }}>
            <tr>
              {data.columns.map(col => (
                <th key={col} style={{ padding: '12px 16px', fontWeight: 600, whiteSpace: 'nowrap', borderRight: '1px solid var(--border)' }} title={col}>
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.data.map((row, i) => (
              <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                {data.columns.map(col => (
                  <td key={`${i}-${col}`} style={{ padding: '12px 16px', whiteSpace: 'nowrap', maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', borderRight: '1px solid var(--border)' }} title={String(row[col])}>
                    {String(row[col])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <section className="section" style={{ paddingTop: 0 }}>
      <div className="container" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 className="mono" style={{ fontSize: '1rem', color: 'var(--text-primary)', marginBottom: '0.25rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Database size={20} color="var(--data)" /> DATASET EXPLORER
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              Upload and search tabular data for open-source intelligence.
            </p>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={handleFileUpload}
              style={{ display: 'none' }} 
              accept=".csv,.xlsx,.xls,.json" 
            />
            <button 
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="mono"
              style={{
                background: 'transparent', border: '1px solid var(--border-accent)', color: 'var(--accent)',
                padding: '8px 16px', fontSize: '0.65rem', cursor: uploading ? 'not-allowed' : 'pointer', textTransform: 'uppercase',
                display: 'flex', alignItems: 'center', gap: '8px', opacity: uploading ? 0.6 : 1, transition: 'all 0.2s ease'
              }}
              onMouseEnter={(e) => {
                if(!uploading) {
                  e.currentTarget.style.color = 'var(--bg-primary)';
                  e.currentTarget.style.background = 'var(--accent)';
                }
              }}
              onMouseLeave={(e) => {
                if(!uploading) {
                  e.currentTarget.style.color = 'var(--accent)';
                  e.currentTarget.style.background = 'transparent';
                }
              }}
            >
              {uploading ? <Loader2 size={14} style={{ animation: 'pulse 1.5s infinite' }} /> : <UploadCloud size={14} />}
              {uploading ? 'UPLOADING...' : 'UPLOAD DATASET'}
            </button>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(250px, 1fr) 3fr', gap: '1.5rem', alignItems: 'start' }}>
          {/* Sidebar */}
          <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: '4px', padding: '16px' }}>
            <h3 className="mono" style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginBottom: '12px', textTransform: 'uppercase' }}>AVAILABLE DATASETS</h3>
            {datasets.length === 0 ? (
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>No datasets available.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {datasets.map(ds => (
                  <button
                    key={ds.id}
                    onClick={() => setSelectedDataset(ds.id)}
                    style={{
                      display: 'flex', alignItems: 'center', gap: '8px', padding: '10px',
                      background: selectedDataset === ds.id ? 'var(--bg-hover)' : 'transparent',
                      border: `1px solid ${selectedDataset === ds.id ? 'var(--border-accent)' : 'transparent'}`,
                      color: selectedDataset === ds.id ? 'var(--text-primary)' : 'var(--text-secondary)',
                      borderRadius: '4px', cursor: 'pointer', textAlign: 'left', transition: 'all 0.2s'
                    }}
                    onMouseEnter={e => {
                      if(selectedDataset !== ds.id) e.currentTarget.style.background = 'var(--bg-hover)';
                    }}
                    onMouseLeave={e => {
                      if(selectedDataset !== ds.id) e.currentTarget.style.background = 'transparent';
                    }}
                  >
                    {ds.name.endsWith('.csv') || ds.name.endsWith('.xlsx') ? (
                      <FileSpreadsheet size={16} />
                    ) : (
                      <FileJson size={16} />
                    )}
                    <span style={{ fontSize: '0.85rem', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{ds.name}</span>
                    <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }} className="mono">{ds.size_mb} MB</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Main Area */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', minWidth: 0 }}>
            {error && (
              <div style={{ background: 'var(--danger-dim)', border: '1px solid var(--danger)', color: '#fff', padding: '12px', borderRadius: '4px', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <AlertCircle size={16} /> {error}
              </div>
            )}

            {!selectedDataset ? (
              <div style={{ border: '1px dashed var(--border)', borderRadius: '4px', padding: '48px 24px', textAlign: 'center', color: 'var(--text-muted)' }}>
                <Database size={48} style={{ opacity: 0.2, marginBottom: '16px', display: 'inline-block' }} />
                <p style={{ fontSize: '0.9rem' }}>Select a dataset from the sidebar or upload a new one to begin.</p>
              </div>
            ) : (
              <>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <div style={{ position: 'relative', flex: 1 }}>
                    <Search size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
                    <input
                      type="text"
                      value={keyword}
                      onChange={(e) => setKeyword(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleSearch(1)}
                      placeholder="Search keywords in dataset..."
                      style={{
                        width: '100%', background: 'var(--bg-elevated)', border: '1px solid var(--border)',
                        color: 'var(--text-primary)', padding: '10px 12px 10px 36px', borderRadius: '4px',
                        fontSize: '0.9rem', outline: 'none'
                      }}
                      onFocus={e => e.currentTarget.style.borderColor = 'var(--data)'}
                      onBlur={e => e.currentTarget.style.borderColor = 'var(--border)'}
                    />
                  </div>
                  <button
                    onClick={() => handleSearch(1)}
                    disabled={loading}
                    className="mono"
                    style={{
                      background: 'var(--bg-elevated)', border: '1px solid var(--border)', color: 'var(--text-primary)',
                      padding: '0 24px', borderRadius: '4px', cursor: 'pointer', fontSize: '0.7rem', textTransform: 'uppercase'
                    }}
                    onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
                    onMouseLeave={e => e.currentTarget.style.background = 'var(--bg-elevated)'}
                  >
                    Search
                  </button>
                </div>

                {loading ? (
                  <div style={{ padding: '64px 0', textAlign: 'center' }}>
                    <p className="mono" style={{ color: 'var(--data)', fontSize: '0.85rem' }}>{'>'} querying dataset<span className="dots"></span></p>
                  </div>
                ) : (
                  <div>
                    {data && (
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '8px' }}>
                        <span className="mono">FOUND {data.total_records.toLocaleString()} ROWS</span>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                          <span className="mono">PAGE {page} OF {totalPages}</span>
                          <div style={{ display: 'flex', gap: '4px' }}>
                            <button 
                              disabled={page <= 1}
                              onClick={() => handleSearch(page - 1)}
                              style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', color: 'var(--text-secondary)', padding: '4px 8px', borderRadius: '4px', cursor: page <= 1 ? 'not-allowed' : 'pointer', fontSize: '0.7rem' }}
                            >
                              PREV
                            </button>
                            <button 
                              disabled={page >= totalPages}
                              onClick={() => handleSearch(page + 1)}
                              style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', color: 'var(--text-secondary)', padding: '4px 8px', borderRadius: '4px', cursor: page >= totalPages ? 'not-allowed' : 'pointer', fontSize: '0.7rem' }}
                            >
                              NEXT
                            </button>
                          </div>
                        </div>
                      </div>
                    )}
                    {renderTable()}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
