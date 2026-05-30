import ExcelJS from 'exceljs'
import { saveAs } from 'file-saver'

function ensureXlsxExtension(filename: string): string {
  return filename.toLowerCase().endsWith('.xlsx') ? filename : `${filename}.xlsx`
}

async function writeWorkbookToFile(workbook: ExcelJS.Workbook, filename: string): Promise<void> {
  const buffer = await workbook.xlsx.writeBuffer()
  const blob = new Blob([buffer], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  })
  saveAs(blob, ensureXlsxExtension(filename))
}

/** JSON 行数组导出为 .xlsx（列顺序以首行键为准） */
export async function downloadExcelFromJson(
  rows: Record<string, string | number>[],
  sheetName: string,
  filename: string,
): Promise<void> {
  const workbook = new ExcelJS.Workbook()
  const worksheet = workbook.addWorksheet(sheetName)
  if (rows.length > 0) {
    const headers = Object.keys(rows[0]!)
    worksheet.addRow(headers)
    for (const row of rows) {
      worksheet.addRow(headers.map((key) => row[key] ?? ''))
    }
  }
  await writeWorkbookToFile(workbook, filename)
}

/** 二维数组（含表头）导出为 .xlsx */
export async function downloadExcelFromAoa(
  aoa: (string | number)[][],
  sheetName: string,
  filename: string,
): Promise<void> {
  const workbook = new ExcelJS.Workbook()
  const worksheet = workbook.addWorksheet(sheetName)
  for (const row of aoa) {
    worksheet.addRow(row)
  }
  await writeWorkbookToFile(workbook, filename)
}
