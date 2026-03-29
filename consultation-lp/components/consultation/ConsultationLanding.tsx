import Header from '@/components/shared/Header'
import Footer from '@/components/shared/Footer'
import HeroSection from '@/components/consultation/HeroSection'
import TrustStripSection from '@/components/consultation/TrustStripSection'
import CasesSection from '@/components/consultation/CasesSection'
import ConsultationCTASection from '@/components/consultation/ConsultationCTASection'
import FAQSection from '@/components/consultation/FAQSection'

export default function ConsultationLanding() {
  return (
    <>
      <Header />
      <main className="main-below-fixed-header">
        <HeroSection />
        <TrustStripSection />
        <CasesSection />
        <ConsultationCTASection variant="after-cases" />
        <FAQSection />
        <ConsultationCTASection variant="final" />
      </main>
      <Footer />
    </>
  )
}
