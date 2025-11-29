import { useMemo } from "react";
import { useTable } from "@tanstack/react-table";

type Row = {
  user_id?: string;
  is_anomaly?: boolean;
  anomaly_score?: number;
  action_taken?: string;
  timestamp?: string;
};

interface Props {
  rows: Row[];
}

export function ComplexTable({ rows }: Props) {
  const data = useMemo(() => rows, [rows]);
  const columns = useMemo(
    () => [
      { header: "User", accessorKey: "user_id" },
      { header: "Anomaly", accessorKey: "is_anomaly" },
      { header: "Score", accessorKey: "anomaly_score" },
      { header: "Action", accessorKey: "action_taken" },
    ],
    []
  );

  const table = useTable({ data, columns });

  return (
    <table className="w-full table-auto text-left text-sm">
      <thead className="text-slate-400">
        {table.getHeaderGroups().map((headerGroup) => (
          <tr key={headerGroup.id}>
            {headerGroup.headers.map((header) => (
              <th key={header.id} className="pb-2">
                {header.isPlaceholder ? null : header.column.columnDef.header?.toString()}
              </th>
            ))}
          </tr>
        ))}
      </thead>
      <tbody className="divide-y divide-white/5">
        {table.getRowModel().rows.map((row) => (
          <tr key={row.id}>
            {row.getVisibleCells().map((cell) => (
              <td key={cell.id} className="py-2 text-white">
                {cell.renderValue() as string}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
