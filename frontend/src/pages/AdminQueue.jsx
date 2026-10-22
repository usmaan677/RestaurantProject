import { useEffect, useState } from "react";

function AdminQueue() {
  const adminEmail = JSON.parse(localStorage.getItem("user") || "null")?.email;
  const [services, setServices] = useState([]);
  const [selectedServiceId, setSelectedServiceId] = useState("");
  const [queue, setQueue] = useState([]);
  const [loadingServices, setLoadingServices] = useState(true);
  const [loadingQueue, setLoadingQueue] = useState(false);
  const [serving, setServing] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    let isActive = true;

    async function loadServices() {
      try {
        const response = await fetch("/api/services/");
        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.detail || "Could not load services.");
        }

        if (isActive) {
          setServices(data);
          setSelectedServiceId(data.length ? String(data[0].id) : "");
        }
      } catch (err) {
        if (isActive) {
          setError(err.message || "Could not connect to the backend.");
        }
      } finally {
        if (isActive) {
          setLoadingServices(false);
        }
      }
    }

    loadServices();
    return () => {
      isActive = false;
    };
  }, []);

  useEffect(() => {
    if (!selectedServiceId || !adminEmail) return;

    let isActive = true;

    async function loadQueue() {
      try {
        setLoadingQueue(true);
        setError("");
        const response = await fetch(
          `/api/queues/${selectedServiceId}/admin?email=${encodeURIComponent(adminEmail)}`,
        );
        const data = await response.json();

        if (!response.ok) {
          throw new Error(
            Array.isArray(data.detail)
              ? data.detail.map((item) => item.msg).join(", ")
              : data.detail || "Could not load the queue.",
          );
        }

        if (isActive) {
          setQueue(data);
        }
      } catch (err) {
        if (isActive) {
          setError(err.message || "Could not connect to the backend.");
        }
      } finally {
        if (isActive) {
          setLoadingQueue(false);
        }
      }
    }

    loadQueue();
    return () => {
      isActive = false;
    };
  }, [selectedServiceId, adminEmail]);

  async function serveNext() {
    if (!selectedServiceId || !adminEmail || queue.length === 0) return;

    setServing(true);
    setError("");
    setNotice("");

    try {
      const response = await fetch(
        `/api/queues/${selectedServiceId}/serve-next`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: adminEmail }),
        },
      );
      const served = await response.json();

      if (!response.ok) {
        throw new Error(
          Array.isArray(served.detail)
            ? served.detail.map((item) => item.msg).join(", ")
            : served.detail || "Could not serve the next user.",
        );
      }

      setNotice(`${served.email} is being served.`);

      const queueResponse = await fetch(
        `/api/queues/${selectedServiceId}/admin?email=${encodeURIComponent(adminEmail)}`,
      );
      const updatedQueue = await queueResponse.json();

      if (!queueResponse.ok) {
        throw new Error(
          Array.isArray(updatedQueue.detail)
            ? updatedQueue.detail.map((item) => item.msg).join(", ")
            : updatedQueue.detail || "Could not refresh the queue.",
        );
      }

      setQueue(updatedQueue);
    } catch (err) {
      setError(err.message || "Could not connect to the backend.");
    } finally {
      setServing(false);
    }
  }

  const selectedService = services.find(
    (service) => String(service.id) === selectedServiceId,
  );

  return (
    <main className="mx-auto max-w-2xl p-6">
      <h1 className="text-3xl font-bold text-slate-800">Manage Queues</h1>
      <p className="mt-2 text-slate-600">
        View and serve users waiting for each service.
      </p>

      {loadingServices && <p className="mt-6">Loading services...</p>}
      {error && <p className="mt-4 text-red-600" role="alert">{error}</p>}

      {!loadingServices && services.length === 0 ? (
        <p className="mt-6 text-slate-600">No services are available.</p>
      ) : (
        !loadingServices && (
          <>
            <label
              htmlFor="service"
              className="mt-6 block text-sm font-medium text-slate-700"
            >
              Service
            </label>
            <select
              id="service"
              value={selectedServiceId}
              onChange={(event) => {
                setSelectedServiceId(event.target.value);
                setNotice("");
                setError("");
              }}
              className="mt-2 w-full rounded-md border border-slate-300 bg-white px-3 py-2"
            >
              {services.map((service) => (
                <option key={service.id} value={service.id}>
                  {service.name}
                </option>
              ))}
            </select>

            <section className="mt-6 rounded-lg border border-slate-200 bg-white p-4">
              <div className="flex items-center justify-between gap-4">
                <h2 className="text-xl font-semibold text-slate-800">
                  {selectedService?.name} queue
                </h2>
                <button
                  type="button"
                  onClick={serveNext}
                  disabled={queue.length === 0 || loadingQueue || serving}
                  className="rounded-md bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
                >
                  {serving ? "Serving..." : "Serve next"}
                </button>
              </div>

              {notice && (
                <p className="mt-3 text-sm text-green-700" role="status">
                  {notice}
                </p>
              )}

              {loadingQueue ? (
                <p className="mt-6 text-slate-500">Loading queue...</p>
              ) : queue.length === 0 ? (
                <p className="mt-6 text-slate-500">This queue is empty.</p>
              ) : (
                <ol className="mt-4 divide-y divide-slate-200">
                  {queue.map((person, index) => (
                    <li
                      key={person.id}
                      className="flex items-center justify-between gap-4 py-3"
                    >
                      <div>
                        <span className="mr-3 text-sm text-slate-500">
                          {index + 1}.
                        </span>
                        <span className="font-medium text-slate-800">
                          {person.email}
                        </span>
                        <p className="ml-7 mt-1 text-sm text-slate-500">
                          Priority {person.priority} · estimated wait{" "}
                          {person.estimated_wait} minutes
                        </p>
                      </div>
                    </li>
                  ))}
                </ol>
              )}
            </section>
          </>
        )
      )}
    </main>
  );
}

export default AdminQueue;
