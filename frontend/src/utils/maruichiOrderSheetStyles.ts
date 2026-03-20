/** 丸一注文書：印刷・html2canvas 用の共通スタイル */
export const MARUICHI_ORDER_SHEET_STYLES = `
            body {
              font-family: 'Meiryo', 'Yu Gothic', sans-serif;
              margin: 0.5cm;
              font-size: 10pt;
              line-height: 1.4;
              background-color: #ffffff;
              color: #000000;
            }
            .order-sheet {
              width: 100%;
              margin: 0 auto;
            }
            .header {
              margin-bottom: 1mm;
              position: relative;
            }
            .issued-info {
              text-align: left;
              font-size: 9pt;
              margin-bottom: 1mm;
            }
            .title {
              text-align: center;
              font-size: 20pt;
              font-weight: bold;
              margin: 1mm 0;
              color: #000000;
              text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
              letter-spacing: 2px;
            }
            .info-row {
              display: flex;
              justify-content: space-between;
              margin-bottom: 2mm;
            }
            .info-item {
              flex: 1;
            }
            .info-item.right {
              text-align: right;
            }
            .recipient-block {
              margin-bottom: 4mm;
              margin-top: 4mm;
            }
            .recipient-block div {
              margin-bottom: 2mm;
              font-size: 18pt;
              font-weight: bold;
              color: #000000;
            }
            .sender-block {
              text-align: right;
              margin-bottom: 1mm;
              margin-top: -12mm;
            }
            .sender-block div {
              margin-bottom: 2mm;
              font-size: 10pt;
              color: #000000;
            }
            .approval-box {
              border: 2px solid #34495e;
              width: 120px;
              margin-left: auto;
              text-align: center;
              margin-top: 1mm;
              border-collapse: collapse;
              border-radius: 4px;
              box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .approval-box table {
              width: 100%;
              border-collapse: collapse;
              margin: 0;
            }
            .approval-box td {
              border: 1px solid #34495e;
              padding: 1mm;
              text-align: center;
              font-size: 8pt;
              width: 50%;
              background-color: #f8f9fa;
              font-weight: 500;
            }
            .delivery-info {
              margin: 5mm 0;
              display: flex;
              justify-content: space-between;
            }
            .delivery-info div {
              font-size: 13pt;
              font-weight: bold;
              color: #000000;
            }
            table {
              width: 100%;
              border-collapse: collapse;
              margin: 2mm 0;
              box-shadow: 0 2px 8px rgba(0,0,0,0.1);
              border-radius: 6px;
              overflow: hidden;
            }
            th, td {
              border: 1px solid #dee2e6;
              padding: 2mm 3mm;
              text-align: left;
              font-size: 9pt;
            }
            th {
              background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
              text-align: center;
              font-weight: bold;
              color: #000000;
              border-bottom: 2px solid #dee2e6;
            }
            .text-center {
              text-align: center;
            }
            .text-right {
              text-align: right;
            }
            .summary-row {
              display: flex;
              justify-content: flex-end;
              margin-top: 4mm;
              gap: 8mm;
              padding: 4mm 0;
              border-top: 2px solid #dee2e6;
              background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
              border-radius: 6px;
              padding: 4mm 8mm;
            }
            .summary-item {
              font-weight: bold;
              font-size: 11pt;
              color: #2c3e50;
              padding: 2mm 4mm;
              background-color: #ffffff;
              border-radius: 4px;
              box-shadow: 0 1px 3px rgba(0,0,0,0.1);
              border: 1px solid #dee2e6;
            }
            .notes {
              margin-top: 12mm;
              font-size: 9pt;
              line-height: 1.6;
              position: absolute;
              bottom: 0.5cm;
              left: 0.5cm;
              right: 0.5cm;
              background-color: #f8f9fa;
              padding: 4mm 6mm;
              border-radius: 6px;
              border-left: 4px solid #6c757d;
              box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .notes p {
              margin: 2mm 0;
              color: #495057;
              font-weight: 400;
            }
            .notes p:first-child {
              margin-top: 0;
            }
            .notes p:last-child {
              margin-bottom: 0;
            }
            body.order-pdf-capture .notes {
              position: relative !important;
              bottom: auto !important;
              left: auto !important;
              right: auto !important;
              margin-top: 8mm !important;
            }
            @page {
              size: A4;
              margin: 0.5cm;
            }
`
