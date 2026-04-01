import { Router } from "express";
import { pool as db } from "../db/connection.js";
import fs from "fs";
import path from "path";
import csv from "csv-parser";
import { fileURLToPath } from "url";
import iconv from "iconv-lite";

const router = Router();
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * 获取棚卸数据列表
 * GET /api/inventory-logs
 */
router.get("/inventory-logs", async (req, res) => {
  try {
    const {
      item,
      keyword = "",
      dateRange = [],
      monthPicker,
      stageType,
      page = 1,
      pageSize = 20,
      sortBy = "log_date",
      sortOrder = "desc",
    } = req.query;

    const limit = Number(pageSize);
    const offset = (Number(page) - 1) * limit;

    const conditions = [];
    const values = [];

    // 添加筛选条件
    if (item) {
      conditions.push("i.item = ?");
      values.push(item);
    }

    if (keyword) {
      conditions.push("(i.product_cd LIKE ? OR i.product_name LIKE ?)");
      values.push(`%${keyword}%`, `%${keyword}%`);
    }

    if (dateRange && dateRange.length === 2) {
      conditions.push("i.log_date BETWEEN ? AND ?");
      values.push(dateRange[0], dateRange[1]);
    }

    if (stageType && stageType !== "all") {
      // 根据stageType筛选对应的工程CD
      const stageTypeMap = {
        cutting: "KT01",
        surface: "KT02",
        sw: "KT03",
        forming: "KT04",
        plating: "KT05",
        welding: "KT07",
        inspection: "KT09",
        warehouse: "KT13",
        outsource_plating: "KT06",
        outsource_welding: "KT08",
        pre_welding_inspection: "KT11",
        pre_outsource_inspection: "KT10",
      };

      const processCd = stageTypeMap[stageType];
      if (processCd) {
        conditions.push("i.process_cd = ?");
        values.push(processCd);
      }
    }

    const whereClause = conditions.length ? "WHERE " + conditions.join(" AND ") : "";

    // 获取总数
    const countSql = `SELECT COUNT(*) as total FROM inventory_logs i ${whereClause}`;
    const [countResult] = await db.query(countSql, values);
    const total = countResult[0].total;

    // 构建排序条件
    const sortFieldMap = {
      product_name: "i.product_name",
      product_cd: "i.product_cd",
      log_date: "i.log_date",
      quantity: "i.quantity",
      process_name: "COALESCE(p.process_name, i.process_cd)",
      created_at: "i.created_at",
    };

    const validSortBy = sortFieldMap[sortBy] || "i.log_date";
    const validSortOrder = sortOrder === "asc" ? "ASC" : "DESC";

    // 获取数据
    const dataSql = `
      SELECT
        i.id,
        i.item,
        i.product_cd,
        i.product_name,
        i.process_cd,
        COALESCE(p.process_name, i.process_cd) as process_name,
        i.log_date,
        i.log_time,
        i.hd_no,
        i.pack_qty,
        i.case_qty,
        i.quantity,
        i.remarks,
        COALESCE(u.name, i.remarks) as worker_name,
        i.created_at,
        i.updated_at
      FROM inventory_logs i
      LEFT JOIN processes p ON i.process_cd = p.process_cd COLLATE utf8mb4_unicode_ci
      LEFT JOIN users u ON i.remarks = u.username COLLATE utf8mb4_unicode_ci
      ${whereClause}
      ORDER BY ${validSortBy} ${validSortOrder}, i.id DESC
      LIMIT ? OFFSET ?
    `;

    const [list] = await db.query(dataSql, [...values, limit, offset]);

    // 计算数量合计
    const totalQuantitySql = `
      SELECT COALESCE(SUM(i.quantity), 0) as totalQuantity
      FROM inventory_logs i
      ${whereClause}
    `;
    const [totalQuantityResult] = await db.query(totalQuantitySql, values);
    const totalQuantity = totalQuantityResult[0].totalQuantity || 0;

    res.json({
      success: true,
      message: "データ取得成功",
      data: {
        list: list || [],
        total: total || 0,
        totalQuantity: totalQuantity,
      },
    });
  } catch (error) {
    console.error("棚卸データ取得エラー:", error);
    res.status(500).json({
      success: false,
      message: "棚卸データの取得に失敗しました",
      error: error.message,
    });
  }
});

/**
 * 删除棚卸数据
 * DELETE /api/inventory-logs/:id
 */
router.delete("/inventory-logs/:id", async (req, res) => {
  try {
    const { id } = req.params;

    const deleteSql = "DELETE FROM inventory_logs WHERE id = ?";
    const [result] = await db.query(deleteSql, [id]);

    if (result.affectedRows === 0) {
      return res.status(404).json({
        success: false,
        message: "指定されたデータが見つかりません",
      });
    }

    res.json({
      success: true,
      message: "データを削除しました",
    });
  } catch (error) {
    console.error("棚卸データ削除エラー:", error);
    res.status(500).json({
      success: false,
      message: "データの削除に失敗しました",
      error: error.message,
    });
  }
});

/**
 * 处理单个CSV文件的导入
 * @param {string} csvFilePath - CSV文件路径
 * @param {string} fileName - 文件名（用于日志）
 * @returns {Promise<{totalProcessed: number, newRecords: number, duplicates: number, errors: number}>}
 */
async function processCSVFile(csvFilePath, fileName) {
  const results = [];
  const duplicates = [];
  const newRecords = [];
  let errors = 0;

  // 检查文件是否存在
  if (!fs.existsSync(csvFilePath)) {
    console.warn(`ファイルが見つかりません: ${csvFilePath}`);
    return {
      totalProcessed: 0,
      newRecords: 0,
      duplicates: 0,
      errors: 0,
      fileExists: false,
    };
  }

  // 读取CSV文件
  await new Promise((resolve, reject) => {
    fs.createReadStream(csvFilePath)
      .pipe(iconv.decodeStream("shift_jis"))
      .pipe(csv())
      .on("data", (data) => {
        results.push(data);
      })
      .on("end", resolve)
      .on("error", reject);
  });

  console.log(`${fileName} から ${results.length} 件のデータを読み込みました`);

  // 处理每一行数据
  for (const row of results) {
    try {
      // 数据清洗和转换
      const originalProcessCd = row["工程CD"]?.trim() || "";
      const paddedProcessCd = originalProcessCd.padStart(2, "0"); // 不足两位数时十位补0

      const cleanData = {
        item: row["項目"]?.trim() || "",
        product_cd: row["製品CD"]?.trim() || "",
        product_name: row["製品名"]?.trim() || "",
        process_cd: `KT${paddedProcessCd}`,
        log_date: row["日付"]?.trim() || "",
        log_time: row["時間"]?.trim() || "",
        hd_no: row["HDNo"]?.trim() || null,
        pack_qty: null,
        case_qty: null,
        quantity: null,
        remarks: row["担当者CD"]?.trim() || null, // 使用担当者CD作为remarks
      };

      // 根据工程CD处理数量字段
      const rawQuantity = parseInt(row["数量"]) || 0;

      if (originalProcessCd === "13") {
        // 工程CD是13：数量写入case_qty，pack_qty从products表获取
        cleanData.case_qty = rawQuantity;

        // 从products表获取unit_per_box作为pack_qty
        try {
          const packQtySql = "SELECT unit_per_box FROM products WHERE product_cd = ?";
          const [packQtyResult] = await db.query(packQtySql, [cleanData.product_cd]);

          if (packQtyResult.length > 0 && packQtyResult[0].unit_per_box) {
            cleanData.pack_qty = packQtyResult[0].unit_per_box;
            cleanData.quantity = cleanData.case_qty * cleanData.pack_qty;
          } else {
            // 如果products表中没有找到，使用默认值1
            cleanData.pack_qty = 1;
            cleanData.quantity = cleanData.case_qty;
            console.warn(
              `製品CD ${cleanData.product_cd} のunit_per_boxが見つかりません。デフォルト値1を使用します。`,
            );
          }
        } catch (packQtyError) {
          console.error(`製品CD ${cleanData.product_cd} のunit_per_box取得エラー:`, packQtyError);
          cleanData.pack_qty = 1;
          cleanData.quantity = cleanData.case_qty;
        }
      } else {
        // 工程CD不是13：数量直接写入quantity
        cleanData.quantity = rawQuantity;
      }

      // 验证必要字段
      if (
        !cleanData.item ||
        !cleanData.product_cd ||
        !cleanData.product_name ||
        !cleanData.log_date
      ) {
        console.warn("必須フィールドが不足しているデータをスキップ:", cleanData);
        errors++;
        continue;
      }

      // 检查重复数据
      const duplicateCheckSql = `
        SELECT id FROM inventory_logs
        WHERE item = ? AND product_cd = ? AND product_name = ? AND log_date = ? AND log_time = ?
      `;
      const [existingRecords] = await db.query(duplicateCheckSql, [
        cleanData.item,
        cleanData.product_cd,
        cleanData.product_name,
        cleanData.log_date,
        cleanData.log_time,
      ]);

      if (existingRecords.length > 0) {
        duplicates.push({
          ...cleanData,
          existingId: existingRecords[0].id,
        });
        continue;
      }

      // 插入新数据
      const insertSql = `
        INSERT INTO inventory_logs (
          item, product_cd, product_name, process_cd, log_date, log_time, hd_no, pack_qty, case_qty, quantity, remarks
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `;

      const [insertResult] = await db.query(insertSql, [
        cleanData.item,
        cleanData.product_cd,
        cleanData.product_name,
        cleanData.process_cd,
        cleanData.log_date,
        cleanData.log_time,
        cleanData.hd_no,
        cleanData.pack_qty,
        cleanData.case_qty,
        cleanData.quantity,
        cleanData.remarks,
      ]);

      newRecords.push({
        id: insertResult.insertId,
        ...cleanData,
      });
    } catch (rowError) {
      console.error("行データ処理エラー:", rowError, "データ:", row);
      errors++;
      continue;
    }
  }

  console.log(
    `${fileName} 処理完了: 新規 ${newRecords.length} 件, 重複 ${duplicates.length} 件, エラー ${errors} 件`,
  );

  return {
    totalProcessed: results.length,
    newRecords: newRecords.length,
    duplicates: duplicates.length,
    errors: errors,
    fileExists: true,
  };
}

/**
 * CSV数据导入（处理三个文件：InventoryLog.csv、Partslog.csv 和 Materiallog.csv）
 * POST /api/inventory-logs/import
 */
router.post("/inventory-logs/import", async (req, res) => {
  try {
    const basePath = "\\\\192.168.1.200\\社内共有\\02_生産管理部\\Data\\BT-data\\受信\\";
    const inventoryLogPath = basePath + "InventoryLog.csv";
    const partsLogPath = basePath + "Partslog.csv";
    const materialLogPath = basePath + "Materiallog.csv";

    // 处理三个CSV文件
    const [inventoryResult, partsResult, materialResult] = await Promise.all([
      processCSVFile(inventoryLogPath, "InventoryLog.csv"),
      processCSVFile(partsLogPath, "Partslog.csv"),
      processCSVFile(materialLogPath, "Materiallog.csv"),
    ]);

    // 合并结果
    const totalProcessed =
      inventoryResult.totalProcessed + partsResult.totalProcessed + materialResult.totalProcessed;
    const totalNewRecords =
      inventoryResult.newRecords + partsResult.newRecords + materialResult.newRecords;
    const totalDuplicates =
      inventoryResult.duplicates + partsResult.duplicates + materialResult.duplicates;
    const totalErrors = inventoryResult.errors + partsResult.errors + materialResult.errors;

    // 检查是否有文件不存在
    const missingFiles = [];
    if (!inventoryResult.fileExists) {
      missingFiles.push("InventoryLog.csv");
    }
    if (!partsResult.fileExists) {
      missingFiles.push("Partslog.csv");
    }
    if (!materialResult.fileExists) {
      missingFiles.push("Materiallog.csv");
    }

    // 如果三个文件都不存在，返回错误
    if (missingFiles.length === 3) {
      return res.status(404).json({
        success: false,
        message: "CSVファイルが見つかりません",
        error: `以下のファイルが見つかりません: ${missingFiles.join(", ")}`,
      });
    }

    // 返回导入结果
    const responseMessage =
      missingFiles.length > 0
        ? `CSVデータの取込が完了しました（注意: ${missingFiles.join(", ")} が見つかりませんでした）`
        : `CSVデータの取込が完了しました`;

    res.json({
      success: true,
      message: responseMessage,
      data: {
        totalProcessed: totalProcessed,
        newRecords: totalNewRecords,
        duplicates: totalDuplicates,
        errors: totalErrors,
        summary: {
          totalProcessed: totalProcessed,
          newRecords: totalNewRecords,
          duplicates: totalDuplicates,
          skipped: totalErrors,
        },
        fileDetails: {
          inventoryLog: {
            file: "InventoryLog.csv",
            processed: inventoryResult.totalProcessed,
            newRecords: inventoryResult.newRecords,
            duplicates: inventoryResult.duplicates,
            errors: inventoryResult.errors,
            exists: inventoryResult.fileExists,
          },
          partsLog: {
            file: "Partslog.csv",
            processed: partsResult.totalProcessed,
            newRecords: partsResult.newRecords,
            duplicates: partsResult.duplicates,
            errors: partsResult.errors,
            exists: partsResult.fileExists,
          },
          materialLog: {
            file: "Materiallog.csv",
            processed: materialResult.totalProcessed,
            newRecords: materialResult.newRecords,
            duplicates: materialResult.duplicates,
            errors: materialResult.errors,
            exists: materialResult.fileExists,
          },
        },
      },
    });

    console.log(
      `インポート完了: 合計処理 ${totalProcessed} 件, 新規 ${totalNewRecords} 件, 重複 ${totalDuplicates} 件, エラー ${totalErrors} 件`,
    );
  } catch (error) {
    console.error("CSVインポートエラー:", error);
    res.status(500).json({
      success: false,
      message: "CSVデータの取込に失敗しました",
      error: error.message,
    });
  }
});

/**
 * 获取导入统计信息
 * GET /api/inventory-logs/import-stats
 */
router.get("/inventory-logs/import-stats", async (req, res) => {
  try {
    const csvFilePath =
      "\\\\192.168.1.200\\社内共有\\02_生産管理部\\Data\\BT-data\\受信\\InventoryLog.csv";

    let fileExists = false;
    let fileSize = 0;
    let lastModified = null;

    if (fs.existsSync(csvFilePath)) {
      fileExists = true;
      const stats = fs.statSync(csvFilePath);
      fileSize = stats.size;
      lastModified = stats.mtime;
    }

    // 获取数据库统计
    const [dbStats] = await db.query("SELECT COUNT(*) as total FROM inventory_logs");
    const [recentStats] = await db.query(`
      SELECT
        COUNT(*) as today_count,
        DATE(created_at) as date
      FROM inventory_logs
      WHERE DATE(created_at) = CURDATE()
      GROUP BY DATE(created_at)
    `);

    res.json({
      success: true,
      data: {
        fileInfo: {
          exists: fileExists,
          path: csvFilePath,
          size: fileSize,
          lastModified: lastModified,
        },
        databaseStats: {
          totalRecords: dbStats[0].total,
          todayRecords: recentStats[0]?.today_count || 0,
        },
      },
    });
  } catch (error) {
    console.error("統計情報取得エラー:", error);
    res.status(500).json({
      success: false,
      message: "統計情報の取得に失敗しました",
      error: error.message,
    });
  }
});

/**
 * 创建库存录入记录
 * POST /api/inventory-logs
 */
router.post("/inventory-logs", async (req, res) => {
  try {
    const {
      item,
      product_cd,
      product_name,
      process_cd,
      process_name,
      log_date,
      log_time,
      hd_no,
      pack_qty,
      case_qty,
      quantity,
      remarks,
    } = req.body;

    // 验证必填字段
    if (
      !item ||
      !product_cd ||
      !product_name ||
      !process_cd ||
      !log_date ||
      !log_time ||
      quantity === undefined
    ) {
      return res.status(400).json({
        success: false,
        message: "必須フィールドが不足しています",
      });
    }

    // 处理工程CD格式
    const formattedProcessCd = process_cd.startsWith("KT")
      ? process_cd
      : `KT${process_cd.padStart(2, "0")}`;

    // 插入数据
    const insertSql = `
      INSERT INTO inventory_logs (
        item, product_cd, product_name, process_cd, log_date, log_time,
        hd_no, pack_qty, case_qty, quantity, remarks
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `;

    const [result] = await db.query(insertSql, [
      item,
      product_cd,
      product_name,
      formattedProcessCd,
      log_date,
      log_time,
      hd_no || null,
      pack_qty || null,
      case_qty || null,
      quantity,
      remarks || null,
    ]);

    // 获取插入的记录
    const [newRecord] = await db.query(
      `
      SELECT
        id,
        item,
        product_cd,
        product_name,
        process_cd,
        log_date,
        log_time,
        hd_no,
        pack_qty,
        case_qty,
        quantity,
        remarks,
        created_at,
        updated_at
      FROM inventory_logs
      WHERE id = ?
    `,
      [result.insertId],
    );

    res.json({
      success: true,
      message: "库存记录创建成功",
      data: newRecord[0],
    });
  } catch (error) {
    console.error("库存记录创建エラー:", error);
    res.status(500).json({
      success: false,
      message: "库存记录の作成に失敗しました",
      error: error.message,
    });
  }
});

/**
 * 简单测试API
 * GET /api/inventory/test
 */
router.get("/test", async (req, res) => {
  try {
    console.log("🔍 测试API被调用");
    res.json({
      success: true,
      message: "测试API正常",
      data: { test: "ok" },
    });
  } catch (error) {
    console.error("测试API错误:", error);
    res.status(500).json({
      success: false,
      message: "测试API失败",
      error: error.message,
    });
  }
});

/**
 * 根据工程获取产品列表
 * GET /api/inventory/products-by-process
 */
router.get("/products-by-process", async (req, res) => {
  try {
    const { process_cd } = req.query;

    if (!process_cd) {
      return res.status(400).json({
        success: false,
        message: "工程CDが必要です",
      });
    }

    // 直接执行查询，简化逻辑
    const sql = `
      SELECT
        prs.product_cd,
        COALESCE(p.product_name, prs.product_cd) as product_name
      FROM product_route_steps prs
      LEFT JOIN products p ON prs.product_cd = p.product_cd
      WHERE prs.process_cd = ? AND prs.product_cd LIKE '%1'
      ORDER BY p.product_name
    `;

    const [products] = await db.query(sql, [process_cd]);

    res.json({
      success: true,
      message:
        products.length > 0
          ? "工程別製品リストを取得しました"
          : "該工程の製品が見つかりませんでした",
      data: products,
    });
  } catch (error) {
    console.error("❌ 工程別製品取得エラー:", error);
    res.status(500).json({
      success: false,
      message: "工程別製品の取得に失敗しました",
      error: error.message,
    });
  }
});

/**
 * 获取最近录入记录
 * GET /api/inventory-logs/recent
 */
router.get("/inventory-logs/recent", async (req, res) => {
  try {
    const { limit = 10, hd_no } = req.query;

    let sql = `
      SELECT
        i.id,
        i.item,
        i.product_cd,
        i.product_name,
        i.process_cd,
        COALESCE(p.process_name, i.process_cd) as process_name,
        i.log_date,
        i.log_time,
        i.hd_no,
        i.pack_qty,
        i.case_qty,
        i.quantity,
        i.remarks,
        i.created_at,
        i.updated_at
      FROM inventory_logs i
      LEFT JOIN processes p ON i.process_cd = p.process_cd COLLATE utf8mb4_unicode_ci
    `;

    const params = [];

    // 如果指定了 hd_no 筛选条件
    if (hd_no) {
      sql += ` WHERE i.hd_no = ?`;
      params.push(hd_no);
    }

    sql += ` ORDER BY created_at DESC LIMIT ?`;
    params.push(Number(limit));

    const [records] = await db.query(sql, params);

    res.json({
      success: true,
      message: "最近の記録を取得しました",
      data: records,
    });
  } catch (error) {
    console.error("最近の記録取得エラー:", error);
    res.status(500).json({
      success: false,
      message: "最近の記録の取得に失敗しました",
      error: error.message,
    });
  }
});

/**
 * 获取棚卸繰越数据
 * GET /api/inventory/carryover-data
 */
router.get("/carryover-data", async (req, res) => {
  try {
    const { month, process_cd } = req.query;

    if (!month || !process_cd) {
      return res.status(400).json({
        success: false,
        message: "月份とprocess_cdが必要です",
      });
    }

    // 构建查询SQL - 从inventory_logs表中获取指定月份和工程的数据并汇总
    const sql = `
      SELECT
        i.product_cd,
        i.product_name,
        i.item,
        SUM(i.quantity) as total_quantity,
        CASE
          WHEN i.item LIKE '%材料%' THEN '本'
          WHEN i.item LIKE '%部品%' THEN '個'
          WHEN i.item LIKE '%製品%' THEN '本'
          ELSE '本'
        END as unit,
        CASE
          WHEN ? IN ('KT01','KT02','KT03','KT04','KT05','KT07','KT09','KT11','KT16','KT17') THEN '工程中間在庫'
          WHEN ? IN ('KT06','KT08','KT10','KT12','KT14','KT15') THEN '外注倉庫'
          WHEN ? = 'KT13' THEN '製品倉庫'
          WHEN ? = 'KT18' THEN '部品倉庫'
          WHEN ? = 'KT19' THEN '材料置場'
          ELSE '工程中間在庫'
        END as location_cd
      FROM inventory_logs i
      WHERE DATE_FORMAT(i.log_date, '%Y-%m') = ?
        AND i.process_cd = ?
      GROUP BY i.product_cd, i.product_name, i.item
      HAVING total_quantity > 0
      ORDER BY i.product_cd
    `;

    const [results] = await db.query(sql, [
      process_cd,
      process_cd,
      process_cd,
      process_cd,
      process_cd,
      month,
      process_cd,
    ]);

    res.json({
      success: true,
      message: "棚卸繰越データを取得しました",
      data: results,
    });
  } catch (error) {
    console.error("棚卸繰越データ取得エラー:", error);
    res.status(500).json({
      success: false,
      message: "棚卸繰越データの取得に失敗しました",
      error: error.message,
    });
  }
});

/**
 * 执行棚卸繰越
 * POST /api/inventory/carryover
 */
router.post("/carryover", async (req, res) => {
  try {
    const { month, process_cd, selectedData } = req.body;

    if (!month || !process_cd || !selectedData || !Array.isArray(selectedData)) {
      return res.status(400).json({
        success: false,
        message: "必要なパラメータが不足しています",
      });
    }

    // 计算下个月的第一天
    const nextMonth = new Date(month + "-01");
    nextMonth.setMonth(nextMonth.getMonth() + 1);
    const transactionTime = nextMonth.toISOString().slice(0, 19).replace("T", " ");

    let successCount = 0;
    let errorCount = 0;
    const errors = [];

    // 开始事务
    await db.query("START TRANSACTION");

    try {
      for (const data of selectedData) {
        // 检查重复记录
        const duplicateCheckSql = `
          SELECT id FROM stock_transaction_logs
          WHERE target_cd = ?
            AND process_cd = ?
            AND transaction_type = '初期'
            AND DATE_FORMAT(transaction_time, '%Y-%m') = ?
        `;

        const nextMonthStr = nextMonth.toISOString().slice(0, 7);
        const [existingRecords] = await db.query(duplicateCheckSql, [
          data.product_cd,
          process_cd,
          nextMonthStr,
        ]);

        if (existingRecords.length > 0) {
          errors.push(`製品「${data.product_cd}」の${nextMonthStr}期初在庫は既に存在します`);
          errorCount++;
          continue;
        }

        // 确定stock_type
        let stockType = "製品";
        if (data.item && data.item.includes("材料")) {
          stockType = "材料";
        } else if (data.item && data.item.includes("部品")) {
          stockType = "部品";
        }

        // 确定location_cd
        let locationCd = "工程中間在庫";
        if (
          ["KT01", "KT02", "KT03", "KT04", "KT05", "KT07", "KT09", "KT11", "KT16", "KT17"].includes(
            process_cd,
          )
        ) {
          locationCd = "工程中間在庫";
        } else if (["KT06", "KT08", "KT10", "KT12", "KT14", "KT15"].includes(process_cd)) {
          locationCd = "外注倉庫";
        } else if (process_cd === "KT13") {
          locationCd = "製品倉庫";
        } else if (process_cd === "KT18") {
          locationCd = "部品倉庫";
        } else if (process_cd === "KT19") {
          locationCd = "材料置場";
        }

        // 确定unit
        let unit = "本";
        if (stockType === "材料") {
          unit = "本";
        } else if (stockType === "部品") {
          unit = "個";
        } else if (stockType === "製品") {
          unit = "本";
        }

        // 插入stock_transaction_logs记录
        const insertSql = `
          INSERT INTO stock_transaction_logs (
            stock_type, target_cd, location_cd, process_cd, transaction_type,
            quantity, unit, transaction_time, remarks
          ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        `;

        await db.query(insertSql, [
          stockType,
          data.product_cd,
          locationCd,
          process_cd,
          "初期",
          data.total_quantity,
          unit,
          transactionTime,
          `${month}月末棚卸データ繰越`,
        ]);

        successCount++;
      }

      // 提交事务
      await db.query("COMMIT");

      res.json({
        success: true,
        message: `繰越処理が完了しました。成功: ${successCount}件, エラー: ${errorCount}件`,
        data: {
          successCount,
          errorCount,
          errors,
        },
      });
    } catch (transactionError) {
      // 回滚事务
      await db.query("ROLLBACK");
      throw transactionError;
    }
  } catch (error) {
    console.error("棚卸繰越エラー:", error);
    res.status(500).json({
      success: false,
      message: "棚卸繰越処理に失敗しました",
      error: error.message,
    });
  }
});

/**
 * 获取棚卸繰越履歴
 * GET /api/inventory/carryover-history
 */
router.get("/carryover-history", async (req, res) => {
  try {
    const {
      carryoverMonth,
      process_cd,
      product_cd,
      transaction_type,
      page = 1,
      pageSize = 20,
      sortBy = "transaction_time",
      sortOrder = "desc",
    } = req.query;

    const limit = Number(pageSize);
    const offset = (Number(page) - 1) * limit;

    const conditions = [];
    const values = [];

    // 如果指定了transaction_type，则使用指定的值，否则默认为'初期'
    if (transaction_type) {
      conditions.push("stl.transaction_type = ?");
      values.push(transaction_type);
    } else {
      conditions.push("stl.transaction_type = '初期'");
    }

    // 添加筛选条件
    if (carryoverMonth) {
      conditions.push("DATE_FORMAT(stl.transaction_time, '%Y-%m') = ?");
      values.push(carryoverMonth);
    }

    if (process_cd) {
      conditions.push("stl.process_cd = ?");
      values.push(process_cd);
    }

    if (product_cd) {
      conditions.push("(stl.target_cd LIKE ? OR p.product_name LIKE ?)");
      values.push(`%${product_cd}%`, `%${product_cd}%`);
    }

    const whereClause = "WHERE " + conditions.join(" AND ");

    // 获取总数
    const countSql = `SELECT COUNT(*) as total FROM stock_transaction_logs stl LEFT JOIN products p ON stl.target_cd = p.product_cd ${whereClause}`;
    const [countResult] = await db.query(countSql, values);
    const total = countResult[0].total;

    // 构建排序条件
    const sortFieldMap = {
      target_cd: "stl.target_cd",
      product_name: "p.product_name",
      quantity: "stl.quantity",
      transaction_time: "stl.transaction_time",
      stock_type: "stl.stock_type",
      location_cd: "stl.location_cd",
    };

    const validSortBy = sortFieldMap[sortBy] || "stl.transaction_time";
    const validSortOrder = sortOrder === "asc" ? "ASC" : "DESC";

    // 获取数据
    const dataSql = `
      SELECT
        stl.id,
        stl.stock_type,
        stl.target_cd,
        COALESCE(p.product_name, stl.target_cd) as product_name,
        stl.location_cd,
        stl.process_cd,
        stl.quantity,
        stl.unit,
        stl.transaction_time,
        stl.lot_no,
        stl.operator_name,
        stl.remarks
      FROM stock_transaction_logs stl
      LEFT JOIN products p ON stl.target_cd = p.product_cd
      ${whereClause}
      ORDER BY ${validSortBy} ${validSortOrder}, stl.id DESC
      LIMIT ? OFFSET ?
    `;

    const [list] = await db.query(dataSql, [...values, limit, offset]);

    res.json({
      success: true,
      message: "繰越履歴データを取得しました",
      data: {
        list: list || [],
        total: total || 0,
      },
    });
  } catch (error) {
    console.error("繰越履歴取得エラー:", error);
    res.status(500).json({
      success: false,
      message: "繰越履歴の取得に失敗しました",
      error: error.message,
    });
  }
});

/**
 * 添加繰越记录
 * POST /api/inventory/carryover-history
 */
router.post("/carryover-history", async (req, res) => {
  try {
    const {
      stock_type,
      target_cd,
      process_cd,
      quantity,
      unit,
      transaction_time,
      location_cd,
      lot_no,
      operator_name,
      remarks,
    } = req.body;

    // 验证必填字段
    if (!stock_type || !target_cd || !process_cd || !quantity || !transaction_time) {
      return res.status(400).json({
        success: false,
        message: "必須フィールドが不足しています",
      });
    }

    // 检查重复记录
    const duplicateCheckSql = `
      SELECT id FROM stock_transaction_logs
      WHERE target_cd = ?
        AND process_cd = ?
        AND transaction_type = '初期'
        AND DATE_FORMAT(transaction_time, '%Y-%m') = DATE_FORMAT(?, '%Y-%m')
    `;

    const [existingRecords] = await db.query(duplicateCheckSql, [
      target_cd,
      process_cd,
      transaction_time,
    ]);

    if (existingRecords.length > 0) {
      return res.status(400).json({
        success: false,
        message: "同じ月の期初記録が既に存在します",
      });
    }

    // 插入记录
    const insertSql = `
      INSERT INTO stock_transaction_logs (
        stock_type, target_cd, location_cd, process_cd, transaction_type,
        quantity, unit, transaction_time, lot_no, operator_name, remarks
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `;

    const [result] = await db.query(insertSql, [
      stock_type,
      target_cd,
      location_cd || "工程中間在庫",
      process_cd,
      "初期",
      quantity,
      unit || "本",
      transaction_time,
      lot_no || null,
      operator_name || null,
      remarks || null,
    ]);

    res.json({
      success: true,
      message: "繰越記録を追加しました",
      data: { id: result.insertId },
    });
  } catch (error) {
    console.error("繰越記録追加エラー:", error);
    res.status(500).json({
      success: false,
      message: "繰越記録の追加に失敗しました",
      error: error.message,
    });
  }
});

/**
 * 更新繰越记录
 * PUT /api/inventory/carryover-history/:id
 */
router.put("/carryover-history/:id", async (req, res) => {
  try {
    const { id } = req.params;
    const {
      stock_type,
      target_cd,
      process_cd,
      quantity,
      unit,
      transaction_time,
      location_cd,
      lot_no,
      operator_name,
      remarks,
    } = req.body;

    // 验证必填字段
    if (!stock_type || !target_cd || !process_cd || !quantity || !transaction_time) {
      return res.status(400).json({
        success: false,
        message: "必須フィールドが不足しています",
      });
    }

    // 检查记录是否存在
    const [existingRecord] = await db.query(
      "SELECT id FROM stock_transaction_logs WHERE id = ? AND transaction_type = '初期'",
      [id],
    );

    if (existingRecord.length === 0) {
      return res.status(404).json({
        success: false,
        message: "指定された記録が見つかりません",
      });
    }

    // 检查重复记录（排除当前记录）
    const duplicateCheckSql = `
      SELECT id FROM stock_transaction_logs
      WHERE target_cd = ?
        AND process_cd = ?
        AND transaction_type = '初期'
        AND DATE_FORMAT(transaction_time, '%Y-%m') = DATE_FORMAT(?, '%Y-%m')
        AND id != ?
    `;

    const [duplicateRecords] = await db.query(duplicateCheckSql, [
      target_cd,
      process_cd,
      transaction_time,
      id,
    ]);

    if (duplicateRecords.length > 0) {
      return res.status(400).json({
        success: false,
        message: "同じ月の期初記録が既に存在します",
      });
    }

    // 更新记录
    const updateSql = `
      UPDATE stock_transaction_logs
      SET stock_type = ?, target_cd = ?, location_cd = ?, process_cd = ?,
          quantity = ?, unit = ?, transaction_time = ?, lot_no = ?,
          operator_name = ?, remarks = ?
      WHERE id = ? AND transaction_type = '初期'
    `;

    const [result] = await db.query(updateSql, [
      stock_type,
      target_cd,
      location_cd || "工程中間在庫",
      process_cd,
      quantity,
      unit || "本",
      transaction_time,
      lot_no || null,
      operator_name || null,
      remarks || null,
      id,
    ]);

    if (result.affectedRows === 0) {
      return res.status(404).json({
        success: false,
        message: "更新に失敗しました",
      });
    }

    res.json({
      success: true,
      message: "繰越記録を更新しました",
    });
  } catch (error) {
    console.error("繰越記録更新エラー:", error);
    res.status(500).json({
      success: false,
      message: "繰越記録の更新に失敗しました",
      error: error.message,
    });
  }
});

/**
 * 删除繰越记录
 * DELETE /api/inventory/carryover-history/:id
 */
router.delete("/carryover-history/:id", async (req, res) => {
  try {
    const { id } = req.params;

    const deleteSql =
      "DELETE FROM stock_transaction_logs WHERE id = ? AND transaction_type = '初期'";
    const [result] = await db.query(deleteSql, [id]);

    if (result.affectedRows === 0) {
      return res.status(404).json({
        success: false,
        message: "指定された記録が見つかりません",
      });
    }

    res.json({
      success: true,
      message: "繰越記録を削除しました",
    });
  } catch (error) {
    console.error("繰越記録削除エラー:", error);
    res.status(500).json({
      success: false,
      message: "繰越記録の削除に失敗しました",
      error: error.message,
    });
  }
});

/**
 * 导出繰越履歴
 * GET /api/inventory/carryover-history/export
 */
router.get("/carryover-history/export", async (req, res) => {
  try {
    const {
      carryoverMonth,
      process_cd,
      product_cd,
      transaction_type,
      sortBy = "transaction_time",
      sortOrder = "desc",
    } = req.query;

    const conditions = [];
    const values = [];

    // 如果指定了transaction_type，则使用指定的值，否则默认为'初期'
    if (transaction_type) {
      conditions.push("stl.transaction_type = ?");
      values.push(transaction_type);
    } else {
      conditions.push("stl.transaction_type = '初期'");
    }

    // 添加筛选条件
    if (carryoverMonth) {
      conditions.push("DATE_FORMAT(stl.transaction_time, '%Y-%m') = ?");
      values.push(carryoverMonth);
    }

    if (process_cd) {
      conditions.push("stl.process_cd = ?");
      values.push(process_cd);
    }

    if (product_cd) {
      conditions.push("stl.target_cd LIKE ?");
      values.push(`%${product_cd}%`);
    }

    const whereClause = "WHERE " + conditions.join(" AND ");

    // 构建排序条件
    const sortFieldMap = {
      target_cd: "stl.target_cd",
      quantity: "stl.quantity",
      transaction_time: "stl.transaction_time",
      stock_type: "stl.stock_type",
      location_cd: "stl.location_cd",
    };

    const validSortBy = sortFieldMap[sortBy] || "stl.transaction_time";
    const validSortOrder = sortOrder === "asc" ? "ASC" : "DESC";

    // 获取数据
    const dataSql = `
      SELECT
        stl.stock_type as '在庫種別',
        stl.target_cd as '製品コード',
        COALESCE(p.product_name, stl.target_cd) as '品名',
        stl.location_cd as '保管場所',
        stl.process_cd as '工程CD',
        stl.quantity as '数量',
        stl.unit as '単位',
        stl.transaction_time as '繰越日時',
        stl.lot_no as 'ロット番号',
        stl.operator_name as '操作者',
        stl.remarks as '備考'
      FROM stock_transaction_logs stl
      LEFT JOIN products p ON stl.target_cd = p.product_cd
      ${whereClause}
      ORDER BY ${validSortBy} ${validSortOrder}, stl.id DESC
    `;

    const [data] = await db.query(dataSql, values);

    // 简单的CSV导出
    const headers = [
      "在庫種別",
      "製品コード",
      "品名",
      "保管場所",
      "工程CD",
      "数量",
      "単位",
      "繰越日時",
      "ロット番号",
      "操作者",
      "備考",
    ];
    let csvContent = headers.join(",") + "\n";

    data.forEach((row) => {
      const values = headers.map((header) => {
        const value = row[header] || "";
        // CSV格式处理：如果包含逗号、引号或换行符，需要用引号包围
        if (
          String(value).includes(",") ||
          String(value).includes('"') ||
          String(value).includes("\n")
        ) {
          return `"${String(value).replace(/"/g, '""')}"`;
        }
        return value;
      });
      csvContent += values.join(",") + "\n";
    });

    // 设置响应头
    res.setHeader("Content-Type", "text/csv; charset=utf-8");
    res.setHeader(
      "Content-Disposition",
      `attachment; filename="carryover_history_${new Date().toISOString().slice(0, 10)}.csv"`,
    );

    // 添加BOM以支持Excel中的UTF-8
    res.write("\uFEFF");
    res.end(csvContent);
  } catch (error) {
    console.error("繰越履歴エクスポートエラー:", error);
    res.status(500).json({
      success: false,
      message: "エクスポートに失敗しました",
      error: error.message,
    });
  }
});

export default router;
