import React, { useState, useEffect } from "react";
import {
  Users,
  Plus,
  Search,
  Building2,
  Mail,
  Phone,
  MapPin,
  FileText,
  ArrowRight,
  RefreshCw,
} from "lucide-react";
import { useMetrology } from "../../context/MetrologyContext";

interface Customer {
  id: string;
  name: string;
  code: string;
  contact_name: string;
  email: string;
  phone: string;
  address: string;
  notes: string;
}

export const CustomersWorkspace: React.FC = () => {
  const { setActiveWorkspace } = useMetrology();
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);

  // New customer form
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [contactName, setContactName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");
  const [notes, setNotes] = useState("");

  const fetchCustomers = async () => {
    setLoading(true);
    try {
      const q = search ? `?search=${encodeURIComponent(search)}` : "";
      const res = await fetch(`/api/v8/customers${q}`).then((r) => r.json());
      if (res && res.customers) {
        setCustomers(res.customers);
      }
    } catch (e) {
      console.error("Error fetching customers:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCustomers();
  }, [search]);

  const handleSaveCustomer = async () => {
    if (!name) return;
    try {
      await fetch("/api/v8/customers", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          code: code || name.substring(0, 4).toUpperCase(),
          contact_name: contactName,
          email,
          phone,
          address,
          notes,
        }),
      });
      setShowModal(false);
      setName("");
      setCode("");
      setContactName("");
      setEmail("");
      setPhone("");
      setAddress("");
      setNotes("");
      fetchCustomers();
    } catch (e) {
      console.error("Error saving customer:", e);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-[#f8fafc] overflow-y-auto custom-scrollbar">
      {/* Top Banner */}
      <div className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between shadow-xs">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-blue-50 border border-blue-200 text-blue-700">
            <Users className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold text-slate-900 tracking-tight">
                Customer Master Directory
              </h1>
              <span className="bg-blue-100 text-blue-800 text-[10px] font-bold px-2 py-0.5 rounded-full font-mono">
                LAB REGISTRY
              </span>
            </div>
            <p className="text-xs text-slate-500">
              Manage external client calibration accounts, quality manager contacts, and compliance profiles.
            </p>
          </div>
        </div>

        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition shadow-xs cursor-pointer"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Add New Customer</span>
        </button>
      </div>

      {/* Main Content */}
      <div className="p-6 space-y-5 max-w-7xl mx-auto w-full">
        {/* Search Bar */}
        <div className="bg-white rounded-lg border border-slate-200 p-3 flex items-center justify-between gap-4">
          <div className="flex items-center gap-2 flex-1 max-w-md">
            <Search className="w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by company name, customer code, or contact person..."
              className="text-xs w-full focus:outline-hidden text-slate-800"
            />
          </div>
          <span className="text-xs text-slate-500 font-mono">
            {customers.length} Accounts Registered
          </span>
        </div>

        {/* Customer Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {customers.map((c) => (
            <div
              key={c.id}
              className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs hover:border-slate-300 transition space-y-3 flex flex-col justify-between"
            >
              <div className="space-y-2">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <div className="p-2 rounded-md bg-slate-100 text-slate-700">
                      <Building2 className="w-4 h-4" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-slate-900">{c.name}</h3>
                      <span className="font-mono text-[10px] text-slate-500 font-bold px-1.5 py-0.2 bg-slate-100 rounded">
                        CODE: {c.code}
                      </span>
                    </div>
                  </div>
                  <span className="text-[10px] font-bold font-mono text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                    ACTIVE CLIENT
                  </span>
                </div>

                <div className="space-y-1 text-xs text-slate-600 pt-2 border-t border-slate-100">
                  {c.contact_name && (
                    <div className="font-medium text-slate-800">
                      Contact: <strong>{c.contact_name}</strong>
                    </div>
                  )}
                  {c.email && (
                    <div className="flex items-center gap-1.5 text-slate-500">
                      <Mail className="w-3.5 h-3.5 text-slate-400" />
                      <span>{c.email}</span>
                    </div>
                  )}
                  {c.phone && (
                    <div className="flex items-center gap-1.5 text-slate-500">
                      <Phone className="w-3.5 h-3.5 text-slate-400" />
                      <span>{c.phone}</span>
                    </div>
                  )}
                  {c.address && (
                    <div className="flex items-center gap-1.5 text-slate-500">
                      <MapPin className="w-3.5 h-3.5 text-slate-400" />
                      <span className="truncate">{c.address}</span>
                    </div>
                  )}
                  {c.notes && (
                    <div className="p-2 rounded bg-slate-50 border border-slate-100 text-[11px] text-slate-500 mt-2">
                      {c.notes}
                    </div>
                  )}
                </div>
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                <span className="text-[11px] text-slate-400 font-mono">ID: {c.id}</span>
                <button
                  onClick={() => setActiveWorkspace("jobs")}
                  className="flex items-center gap-1 text-xs font-bold text-blue-600 hover:text-blue-800 transition cursor-pointer"
                >
                  <span>Create Calibration Job</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Add Customer Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-lg w-full p-6 space-y-4 shadow-xl">
            <div className="flex items-center gap-2 text-slate-900 font-bold text-base border-b border-slate-100 pb-3">
              <Building2 className="w-5 h-5 text-blue-600" />
              <span>Register New Client Account</span>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="col-span-2 space-y-1">
                <label className="font-semibold text-slate-700">Company Name *</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Lockheed Martin Space"
                  className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:outline-hidden"
                />
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-slate-700">Client Code</label>
                <input
                  type="text"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  placeholder="e.g. LOCK-SPC"
                  className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:outline-hidden"
                />
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-slate-700">Primary Contact</label>
                <input
                  type="text"
                  value={contactName}
                  onChange={(e) => setContactName(e.target.value)}
                  placeholder="e.g. Dr. Robert Vance"
                  className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:outline-hidden"
                />
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-slate-700">Email Address</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="qa@client.com"
                  className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:outline-hidden"
                />
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-slate-700">Phone</label>
                <input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+1 (555) 000-0000"
                  className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:outline-hidden"
                />
              </div>

              <div className="col-span-2 space-y-1">
                <label className="font-semibold text-slate-700">Laboratory / Facility Address</label>
                <input
                  type="text"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  placeholder="Facility 4, Aerospace Blvd, City, State"
                  className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:outline-hidden"
                />
              </div>

              <div className="col-span-2 space-y-1">
                <label className="font-semibold text-slate-700">Quality / Traceability Notes</label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="e.g. Requires NIST traceable certificate copy on all reports"
                  rows={2}
                  className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:outline-hidden"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
              <button
                onClick={() => setShowModal(false)}
                className="px-3.5 py-1.5 text-xs text-slate-600 hover:text-slate-800 cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveCustomer}
                className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-xs font-bold cursor-pointer"
              >
                Save Client
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
