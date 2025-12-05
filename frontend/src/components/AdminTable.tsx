import React from 'react';
import './AdminTable.css';

export interface Column<T> {
  header: string;
  accessor: keyof T | ((row: T) => React.ReactNode);
  width?: string;
  render?: (row: T) => React.ReactNode;
}

interface AdminTableProps<T> {
  data: T[];
  columns: Column<T>[];
  onEdit?: (item: T) => void;
  onDelete?: (item: T) => void;
  loading?: boolean;
  keyExtractor: (item: T) => string | number;
  customActions?: (item: T) => React.ReactNode;
}

export function AdminTable<T>({
  data,
  columns,
  onEdit,
  onDelete,
  loading,
  keyExtractor,
  customActions,
}: AdminTableProps<T>) {
  if (loading) {
    return <div className="admin-table-loading">Загрузка...</div>;
  }

  if (data.length === 0) {
    return <div className="admin-table-empty">Нет данных</div>;
  }

  return (
    <div className="admin-table-container">
      <table className="admin-table">
        <thead>
          <tr>
            {columns.map((col, idx) => (
              <th key={idx} style={{ width: col.width }}>
                {col.header}
              </th>
            ))}
            {(onEdit || onDelete || customActions) && <th style={{ width: '150px' }}>Действия</th>}
          </tr>
        </thead>
        <tbody>
          {data.map((row) => (
            <tr key={keyExtractor(row)}>
              {columns.map((col, idx) => (
                <td key={idx}>
                  {col.render
                    ? col.render(row)
                    : typeof col.accessor === 'function'
                    ? col.accessor(row)
                    : String(row[col.accessor] ?? '')}
                </td>
              ))}
              {(onEdit || onDelete || customActions) && (
                <td className="admin-table-actions">
                  {customActions ? (
                    customActions(row)
                  ) : (
                    <>
                      {onEdit && (
                        <button
                          className="admin-btn admin-btn-edit"
                          onClick={() => onEdit(row)}
                        >
                          Изменить
                        </button>
                      )}
                      {onDelete && (
                        <button
                          className="admin-btn admin-btn-delete"
                          onClick={() => onDelete(row)}
                        >
                          Удалить
                        </button>
                      )}
                    </>
                  )}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

