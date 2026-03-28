import { NextResponse } from 'next/server'
import { getCasesFromSheet } from '@/lib/googleSheets'

export const dynamic = 'force-dynamic'
export const revalidate = 0

/**
 * スプレッドシートから導入事例を取得するAPI
 */
export async function GET() {
  try {
    const cases = await getCasesFromSheet()

    return NextResponse.json({
      success: true,
      cases,
      count: cases.length,
    })
  } catch (error) {
    console.error('Error in /api/cases:', error)

    return NextResponse.json(
      {
        success: false,
        error: 'Failed to fetch cases',
        cases: [],
        count: 0,
      },
      { status: 500 }
    )
  }
}
