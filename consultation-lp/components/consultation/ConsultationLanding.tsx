import Header from '@/components/shared/Header'
import Footer from '@/components/shared/Footer'
import HeroSection from '@/components/consultation/HeroSection'
import TrustStripSection from '@/components/consultation/TrustStripSection'
import ProblemsSection from '@/components/consultation/ProblemsSection'
import CasesSection from '@/components/consultation/CasesSection'
import ConsultationCTASection from '@/components/consultation/ConsultationCTASection'
import FAQSection from '@/components/consultation/FAQSection'
import ContactForm from '@/components/consultation/ContactForm'

export default function ConsultationLanding() {
  return (
    <>
      <Header />
      <main className="main-below-fixed-header">
        <HeroSection />
        <TrustStripSection />
        <ProblemsSection />
        <CasesSection />
        <ConsultationCTASection variant="after-cases" />
        <FAQSection />
        <ConsultationCTASection variant="after-faq" />

        <section id="contact" className="section-container bg-gradient-to-br from-primary-50 via-white to-accent-50">
          <div className="text-center mb-12">
            <h2 className="section-heading">
              まずは<span className="gradient-text">無料相談</span>から
            </h2>
            <p className="section-subheading">
              現状の業務について、お気軽にご相談ください
              <br />
              無理な営業は一切ありません
            </p>
          </div>

          <div className="max-w-2xl mx-auto mb-10 rounded-[var(--radius-medium)] border border-blue-100 bg-white/90 px-6 py-5 text-center shadow-sm">
            <p className="text-[var(--text-dark)] font-semibold mb-1">ご安心ください</p>
            <p className="text-sm text-[var(--text-gray)] leading-relaxed">
              送信後に<strong className="text-[var(--primary-color)]">無理な営業電話やしつこいフォローは行いません</strong>。
              まずは内容を確認し、必要に応じて日程調整のご連絡のみいたします。
            </p>
          </div>

          <ContactForm />
        </section>
      </main>
      <Footer />
    </>
  )
}
