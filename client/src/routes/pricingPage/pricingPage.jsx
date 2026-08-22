import { PricingTable } from "@clerk/clerk-react";
import { Link } from "react-router-dom";
import { useFeatureFlag } from "../../hooks/useFeatureFlags";
import "./pricingPage.css";

const LIMITS = [
  { feature: "AI messages", free: "10 / minute", pro: "40 / minute" },
  { feature: "Data reads", free: "60 / minute", pro: "240 / minute" },
  { feature: "Edits & shares", free: "30 / minute", pro: "120 / minute" },
];

const PricingPage = () => {
  const { enabled, isLoading } = useFeatureFlag("show_pricing_page");

  // Server-side feature flag gates this page for everyone.
  if (!isLoading && !enabled) {
    return (
      <div className="pricingPage">
        <header className="pricingHeader">
          <h1>Pricing coming soon</h1>
          <p>Plans are not open for subscription yet — check back shortly.</p>
        </header>
      </div>
    );
  }

  return (
    <div className="pricingPage">
      <header className="pricingHeader">
        <h1>Choose your plan</h1>
        <p>Start free. Upgrade when you need more headroom.</p>
      </header>

      <div className="pricingTableWrap">
        <PricingTable newSubscriptionRedirectUrl="/dashboard" />
      </div>

      <section className="limitsCard">
        <h2>What you get</h2>
        <table>
          <thead>
            <tr>
              <th>Rate limit</th>
              <th>Free</th>
              <th>Pro</th>
            </tr>
          </thead>
          <tbody>
            {LIMITS.map((row) => (
              <tr key={row.feature}>
                <td>{row.feature}</td>
                <td>{row.free}</td>
                <td className="proValue">{row.pro}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
};

export default PricingPage;
