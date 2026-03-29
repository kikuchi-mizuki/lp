import { NextResponse } from 'next/server'
import { getCasesFromSheet, getConsultationCasesFallback } from '@/lib/googleSheets'

export const dynamic = 'force-dynamic'
export const revalidate = 0

const ROUTE_TIMEOUT_MS = 12_000

function withTimeout<T>(promise: Promise<T>, ms: number): Promise<T> {
  return new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error(`/api/cases: timeout ${ms}ms`)), ms)
    promise.then(
      (v) => {
        clearTimeout(t)
        resolve(v)
      },
      (e) => {
        clearTimeout(t)
        reject(e)
      }
    )
  })
}

/**
 * スプレッドシートから導入事例を取得するAPI
 * 外部APIのハングでページが永遠に待たないよう、全体にもタイムアウトをかける
 */
export async function GET() {
  try {
    const cases = await withTimeout(getCasesFromSheet(), ROUTE_TIMEOUT_MS)

    return NextResponse.json({
      success: true,
      cases,
      count: cases.length,
    })
  } catch (error) {
    console.error('Error in /api/cases:', error)

    const fallback = getConsultationCasesFallback()

    return NextResponse.json(
      {
        success: true,
        cases: fallback,
        count: fallback.length,
        degraded: true,
        message: 'スプレッドシート取得を待てなかったため、表示用サンプルを返しています。',
      },
      { status: 200 }
    )
  }
}
