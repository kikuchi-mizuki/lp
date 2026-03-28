import { NextRequest, NextResponse } from 'next/server'
import { createServiceClient } from '@/lib/supabase/client'
import type { ConsultationLeadInsert } from '@/types'

export async function POST(request: NextRequest) {
  try {
    const body: ConsultationLeadInsert = await request.json()

    // バリデーション
    if (!body.company_name || !body.name || !body.email || !body.inquiry) {
      return NextResponse.json(
        { error: '必須項目が入力されていません' },
        { status: 400 }
      )
    }

    const supabase = createServiceClient()

    // Supabaseに保存
    const { data, error } = await supabase
      .from('consultation_leads')
      .insert([body])
      .select()
      .single()

    if (error) {
      console.error('Supabase insert error:', error)
      return NextResponse.json(
        { error: 'データベースエラーが発生しました' },
        { status: 500 }
      )
    }

    return NextResponse.json({ success: true, data })
  } catch (error) {
    console.error('Consultation form error:', error)
    return NextResponse.json(
      { error: 'サーバーエラーが発生しました' },
      { status: 500 }
    )
  }
}
