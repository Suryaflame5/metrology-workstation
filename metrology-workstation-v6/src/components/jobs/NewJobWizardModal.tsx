import React, { useState, useEffect } from "react";
import {
  Sparkles,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  X,
  FileSpreadsheet,
  Cpu,
  Users,
  ListOrdered,
  Activity,
  Play,
  Radio,
} from "lucide-react";
import { createJob } from "../../services/jobApi";
import { MeasurementJob } from "../../types/job";

interface WizardProps {
  isOpen: boolean;
  onClose: () => void;
  onJobCreated: (job: MeasurementJob) => void;
}

export const NewJobWizardModal: React.FC<WizardProps> = ({ isOpen, onClose, onJobCreated }) => {
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [loading, setLoading] = useState(false);

  // Catalogs
  const [customers, setCustomers] = useState<any[]>([]);
  const [templates, setTemplates] = useState<any[]>([]);
  const [instruments, setInstruments] = useState<any[]>([]);

  // Step 1: Metadata
  const [title, setTitle] = useState("Precision Calibration Run");
  const [selectedCustomerId, setSelectedCustomerId] = useState("");
  const [customerName, setCustomerName] = useState("Apex Aerospace Systems");
  const [instrumentName, setInstrumentName] = useState("Digital Multimeter 8.5-Digit");
  const [instrumentModel, setInstrumentModel] = useState("Fluke 8508A");
  const [instrumentSerial, setInstrumentSerial] = useState("SN-8508-4109");
  const [selectedTemplateId, setSelectedTemplateId] = useState("PROC-EURAMET-CG-15");
  const [procedureName, setProcedureName] = useState("EURAMET cg-15 Multimeter 10 V DC Calibration");
  const [unit, setUnit] = useState("V");
  const [nominal, setNominal] = useState(10.0);
  const [tolLower, setTolLower] = useState(-0.005);
  const [tolUpper, setTolUpper] = useState(0.005);

  // Step 2: Data Ingestion & Health
  const [rawText, setRawText] = useState("10.0018\n10.0022\n10.0019\n10.0024\n10.0020");
  const [parsedReadings, setParsedReadings] = useState<number[]>([10.0018, 10.0022, 10.0019, 10.0024, 10.0020]);
  const [ambientTemp, setAmbientTemp] = useState(20.0);
  const [humidity, setHumidity] = useState(45.0);
  const [dataHealth, setDataHealth] = useState<any | null>(null);

  // Step 3: Model
  const [suggestedModel, setSuggestedModel] = useState<any | null>(null);

  useEffect(() => {
    if (isOpen) {
      Promise.all([
        fetch("/api/v8/customers").then((r) => r.json()),
        fetch("/api/v8/templates").then((r) => r.json()),
        fetch("/api/v8/instruments").then((r) => r.json()),
      ]).then(([resC, resT, resI]) => {
        if (resC?.customers) setCustomers(resC.customers);
        if (resT?.templates) setTemplates(resT.templates);
        if (resI?.instruments) setInstruments(resI.instruments);
      }).catch(console.error);
    }
  }, [isOpen]);

  const handleTemplateChange = (tId: string) => {
    setSelectedTemplateId(tId);
    const tmpl = templates.find((t) => t.id === tId);
    if (tmpl) {
      setProcedureName(tmpl.title);
      setUnit(tmpl.default_unit);
      setNominal(tmpl.nominal_value);
      setTolLower(tmpl.tolerance_lower);
      setTolUpper(tmpl.tolerance_upper);
      if (tmpl.default_unit === "mm") {
        setRawText("25.0004\n25.0006\n25.0003\n25.0007\n25.0005");
        setParsedReadings([25.0004, 25.0006, 25.0003, 25.0007, 25.0005]);
      } else if (tmpl.default_unit === "bar") {
        setRawText("9.998\n10.001\n9.999\n10.002\n10.000");
        setParsedReadings([9.998, 10.001, 9.999, 10.002, 10.000]);
      } else {
        setRawText("10.0018\n10.0022\n10.0019\n10.0024\n10.0020");
        setParsedReadings([10.0018, 10.0022, 10.0019, 10.0024, 10.0020]);
      }
    }
  };

  const handleValidateStep2 = async () => {
    setLoading(true);
    try {
      const numbers = rawText
        .split(/[\n,;\t]+/)
        .map((s) => parseFloat(s.trim()))
        .filter((n) => !isNaN(n));
      setParsedReadings(numbers);

      const rows = numbers.map((n) => ({ Reading: n }));
      const mapping = { Reading: { role: "measured" } };

      const res = await fetch("/api/v8/wizard/validate-and-model", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          rows,
          mapping,
          nominal,
          tolerance_lower: tolLower,
          tolerance_upper: tolUpper,
          unit,
          measurand: procedureName,
        }),
      }).then((r) => r.json());

      if (res) {
        setDataHealth(res.data_health);
        setSuggestedModel(res.suggested_model);
        setStep(3);
      }
    } catch (e) {
      console.error("Validation error:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleFinalSubmit = async () => {
    setLoading(true);
    try {
      const created = await createJob({
        title,
        customer_name: customerName,
        instrument_name: instrumentName,
        instrument_model: instrumentModel,
        instrument_serial: instrumentSerial,
        procedure_name: procedureName,
        unit,
        nominal_value: nominal,
        tolerance_upper: tolUpper,
        tolerance_lower: tolLower,
        status: "NEW",
        raw_measurements: parsedReadings,
        environment: {
          ambient_temperature_c: ambientTemp,
          relative_humidity_pct: humidity,
          atmospheric_pressure_hpa: 1013.25,
        },
      });

      // Automatically trigger 1-Click Pipeline execution
      try {
        const pipeRes = await fetch(`/api/jobs/${created.id}/run-pipeline`, { method: "POST" });
        const updated = await pipeRes.json();
        onJobCreated(updated.job || created);
      } catch {
        onJobCreated(created);
      }
      onClose();
    } catch (e: any) {
      alert(`Error creating job: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50 backdrop-blur-xs">
      <div className="bg-white rounded-2xl max-w-2xl w-full p-6 space-y-6 shadow-2xl border border-slate-200 flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-blue-50 border border-blue-200 text-blue-700">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900 tracking-tight">
                New Calibration Job Wizard
              </h2>
              <p className="text-xs text-slate-500">
                Step {step} of 3: {step === 1 ? "Identity & Parameters" : step === 2 ? "Data & Health Check" : "Model & Auto-Run"}
              </p>
            </div>
          </div>

          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 p-1">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Step Progression Bar */}
        <div className="flex items-center gap-2">
          <div className={`flex-1 h-1.5 rounded-full ${step >= 1 ? "bg-blue-600" : "bg-slate-200"}`} />
          <div className={`flex-1 h-1.5 rounded-full ${step >= 2 ? "bg-blue-600" : "bg-slate-200"}`} />
          <div className={`flex-1 h-1.5 rounded-full ${step >= 3 ? "bg-blue-600" : "bg-slate-200"}`} />
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto space-y-4 custom-scrollbar pr-1">
          {step === 1 && (
            <div className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div className="col-span-2 space-y-1">
                  <label className="font-semibold text-slate-700">Job Title / Calibration Description</label>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:outline-hidden"
                  />
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-slate-700">Customer / Client</label>
                  <select
                    value={customerName}
                    onChange={(e) => setCustomerName(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-md bg-white focus:outline-hidden"
                  >
                    {customers.map((c) => (
                      <option key={c.id} value={c.name}>
                        {c.name} ({c.code})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-slate-700">Standard Calibration Procedure</label>
                  <select
                    value={selectedTemplateId}
                    onChange={(e) => handleTemplateChange(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-md bg-white focus:outline-hidden font-medium text-slate-800"
                  >
                    {templates.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.code} — {t.title}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-slate-700">Instrument Model</label>
                  <input
                    type="text"
                    value={instrumentModel}
                    onChange={(e) => setInstrumentModel(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-hidden"
                  />
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-slate-700">Instrument Serial Number</label>
                  <input
                    type="text"
                    value={instrumentSerial}
                    onChange={(e) => setInstrumentSerial(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-hidden font-mono"
                  />
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-slate-700">Nominal Target ({unit})</label>
                  <input
                    type="number"
                    step="any"
                    value={nominal}
                    onChange={(e) => setNominal(parseFloat(e.target.value) || 0)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-hidden font-mono"
                  />
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-slate-700">Tolerance Upper (+{unit})</label>
                  <input
                    type="number"
                    step="any"
                    value={tolUpper}
                    onChange={(e) => setTolUpper(parseFloat(e.target.value) || 0)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-hidden font-mono"
                  />
                </div>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4 text-xs">
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="font-semibold text-slate-700">Measurement Observations (Paste or Enter Values)</label>
                  <span className="text-[11px] text-slate-400 font-mono">1 observation per line</span>
                </div>
                <textarea
                  value={rawText}
                  onChange={(e) => setRawText(e.target.value)}
                  rows={5}
                  placeholder="e.g. 10.0018\n10.0022\n10.0019"
                  className="w-full font-mono text-xs p-3 border border-slate-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:outline-hidden"
                />
              </div>

              <div className="grid grid-cols-2 gap-3 p-3 bg-slate-50 rounded-lg border border-slate-200">
                <div className="space-y-1">
                  <label className="font-semibold text-slate-600">Ambient Temperature (°C)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={ambientTemp}
                    onChange={(e) => setAmbientTemp(parseFloat(e.target.value) || 20.0)}
                    className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-md font-mono"
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-semibold text-slate-600">Relative Humidity (%)</label>
                  <input
                    type="number"
                    step="0.5"
                    value={humidity}
                    onChange={(e) => setHumidity(parseFloat(e.target.value) || 45.0)}
                    className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-md font-mono"
                  />
                </div>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4 text-xs">
              {/* Data Health Summary Card */}
              {dataHealth && (
                <div className={`p-4 rounded-xl border space-y-2 ${
                  dataHealth.health_status === "HEALTHY"
                    ? "bg-emerald-50 border-emerald-200 text-emerald-900"
                    : "bg-amber-50 border-amber-200 text-amber-900"
                }`}>
                  <div className="flex items-center justify-between font-bold">
                    <span className="flex items-center gap-1.5">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      Smart Data Health Assessment: {dataHealth.health_status}
                    </span>
                    <span className="font-mono text-[11px]">{dataHealth.valid_rows_count} Valid Readings</span>
                  </div>
                  <p className="text-[11px] opacity-90">{dataHealth.summary}</p>
                </div>
              )}

              {/* Proposed GUM Uncertainty Model */}
              {suggestedModel && (
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
                  <div className="flex items-center justify-between border-b border-slate-200 pb-2">
                    <span className="font-bold text-slate-800 uppercase tracking-wider">
                      Auto-Generated GUM Uncertainty Budget
                    </span>
                    <span className="font-mono font-bold text-blue-700">
                      U95 = ±{suggestedModel.expanded_uncertainty_U95} {unit}
                    </span>
                  </div>

                  <div className="space-y-1.5 font-mono text-[11px]">
                    {suggestedModel.contributors?.map((c: any, i: number) => (
                      <div key={i} className="flex justify-between items-center bg-white px-2.5 py-1.5 rounded border border-slate-100">
                        <span className="text-slate-700 font-sans">{c.name} ({c.type})</span>
                        <span className="text-slate-500 font-bold">±{c.standard_uncertainty} {unit}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Modal Footer Controls */}
        <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
          {step > 1 ? (
            <button
              onClick={() => setStep((s) => (s - 1) as any)}
              className="flex items-center gap-1 px-3 py-1.5 rounded-md border border-slate-300 text-slate-700 text-xs font-semibold hover:bg-slate-50 cursor-pointer"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              Back
            </button>
          ) : (
            <div />
          )}

          {step < 3 ? (
            <button
              onClick={step === 1 ? () => setStep(2) : handleValidateStep2}
              disabled={loading}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition shadow-xs cursor-pointer disabled:opacity-50"
            >
              <span>{step === 1 ? "Next: Ingestion & Health" : "Validate & Propose Model"}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          ) : (
            <button
              onClick={handleFinalSubmit}
              disabled={loading}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition shadow-xs cursor-pointer disabled:opacity-50"
            >
              <Play className="w-4 h-4" />
              <span>Create Job &amp; Run 1-Click Pipeline</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
