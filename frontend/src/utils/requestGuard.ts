/** 非同期読み込みの競合を防ぐ（最新リクエストのみ結果を反映） */
export function createRequestGuard() {
  let latestId = 0
  return {
    start(): number {
      latestId += 1
      return latestId
    },
    isStale(id: number): boolean {
      return id !== latestId
    },
  }
}
