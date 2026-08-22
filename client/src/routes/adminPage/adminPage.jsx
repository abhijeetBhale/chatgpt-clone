import { useState } from "react";
import { useAuth } from "@clerk/clerk-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import "./adminPage.css";

const API_URL = import.meta.env.VITE_API_URL;

const AdminPage = () => {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [error, setError] = useState("");

  // Admin status check happens server-side; non-admins get a 403 here.
  const { isPending, error: loadError, data: flags } = useQuery({
    queryKey: ["adminFlags"],
    queryFn: async () => {
      const token = await getToken();
      const res = await fetch(`${API_URL}/api/admin/flags`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.status === 403) throw new Error("FORBIDDEN");
      if (!res.ok) throw new Error("Failed to load flags");
      return res.json();
    },
  });

  const { data: planModel } = useQuery({
    queryKey: ["planModel"],
    queryFn: async () => {
      const token = await getToken();
      const res = await fetch(`${API_URL}/api/admin/plans`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to load plans");
      return res.json();
    },
  });

  const mutateFlag = async (path, method, body) => {
    setError("");
    const token = await getToken();
    const res = await fetch(`${API_URL}${path}`, {
      method,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!res.ok) {
      const detail = await res.json().catch(() => ({}));
      setError(detail.detail || "Request failed");
      return;
    }
    queryClient.invalidateQueries({ queryKey: ["adminFlags"] });
    queryClient.invalidateQueries({ queryKey: ["featureFlags"] });
  };

  const handleToggle = (flag, enabled) =>
    mutateFlag(`/api/admin/flags/${flag.name}`, "PATCH", { enabled });

  const handleCreate = async (e) => {
    e.preventDefault();
    await mutateFlag("/api/admin/flags", "POST", {
      name: newName.trim(),
      description: newDesc.trim(),
    });
    setNewName("");
    setNewDesc("");
  };

  const handleDelete = (name) => mutateFlag(`/api/admin/flags/${name}`, "DELETE");

  return (
    <div className="adminPage">
      <header className="adminHeader">
        <h1>Feature Flags</h1>
        <p>Toggle features on or off globally — changes apply within ~15 seconds.</p>
      </header>

      {loadError?.message === "FORBIDDEN" ? (
        <div className="adminDenied">
          <h2>403 — Admin access required</h2>
          <p>Your account is not on the admin list.</p>
          <Link to="/dashboard" className="backLink">← Back to dashboard</Link>
        </div>
      ) : isPending ? (
        <p className="adminLoading">Loading flags…</p>
      ) : (
        <>
          <div className="flagList">
            {(flags || []).map((flag) => (
              <div key={flag.name} className={`flagRow ${flag.enabled ? "on" : ""}`}>
                <div className="flagInfo">
                  <code className="flagName">{flag.name}</code>
                  <span className="flagDesc">{flag.description || "No description"}</span>
                </div>
                <button
                  className={`toggleSwitch ${flag.enabled ? "checked" : ""}`}
                  onClick={() => handleToggle(flag, !flag.enabled)}
                  aria-label={`Toggle ${flag.name}`}
                >
                  <span className="knob" />
                </button>
                <button
                  className="deleteBtn"
                  onClick={() => handleDelete(flag.name)}
                  title="Delete flag"
                >
                  ✕
                </button>
              </div>
            ))}
            {flags && flags.length === 0 && (
              <div className="flagEmpty">No flags yet — create one below.</div>
            )}
          </div>

          {error && <p className="flagError">{error}</p>}

          <form className="flagCreate" onSubmit={handleCreate}>
            <input
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="new_flag_name"
              pattern="[a-z0-9_]{2,64}"
              required
            />
            <input
              value={newDesc}
              onChange={(e) => setNewDesc(e.target.value)}
              placeholder="What does this flag gate?"
            />
            <button type="submit" disabled={!newName.trim()}>Add flag</button>
          </form>
        )}

        {planModel && (
          <section className="plansCard">
            <div className="plansCardHeader">
              <h2>Pricing Plans</h2>
              <span className={`plansStateBadge ${planModel.pricing_page_enabled ? "on" : "off"}`}>
                {planModel.pricing_page_enabled ? "Pricing page live" : "Pricing page hidden"}
              </span>
            </div>
            <table>
              <thead>
                <tr>
                  <th>Rate limit</th>
                  <th>Free</th>
                  <th>Pro</th>
                </tr>
              </thead>
              <tbody>
                {planModel.rows.map((row) => (
                  <tr key={row.feature}>
                    <td>{row.feature}</td>
                    <td>{row.free.value} / {row.free.period}</td>
                    <td className="proValue">{row.pro.value} / {row.pro.period}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="plansNote">
              Pro plan slug: <code>{planModel.pro_plan_slug}</code> — price & checkout are managed in the{" "}
              <a href="https://dashboard.clerk.com/~/billing/plans" target="_blank" rel="noreferrer">Clerk Billing dashboard</a>.
              The pricing page itself is gated by the <code>show_pricing_page</code> flag above.
            </p>
          </section>
        )}
        </>
      )}
    </div>
  );
};

export default AdminPage;
